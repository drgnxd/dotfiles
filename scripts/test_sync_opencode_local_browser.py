from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("sync_opencode_local_browser.py")
SPEC = importlib.util.spec_from_file_location("local_browser_sync", SCRIPT)
assert SPEC and SPEC.loader
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class LocalBrowserSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="local-browser-sync-")
        self.home = Path(self.temp.name)
        os.chmod(self.home, 0o700)
        self.config = self.home / ".config"
        self.data = self.home / ".local" / "share"
        self.config.mkdir(mode=0o700)
        self.data.mkdir(parents=True, mode=0o700)
        self.files = {name: ("fixture:" + name).encode() for name in SYNC.SOURCE_FILES}
        self.generation = self._make_generation(self.files)
        self.args = type("Args", (), {
            "home": str(self.home),
            "config_home": str(self.config),
            "data_home": str(self.data),
            "activation_pid": os.getpid(),
            "transaction": None,
        })()

    def tearDown(self):
        self.temp.cleanup()

    def process_probe(self, *args):
        return []

    def test_activation_preserves_parent_shell_owner_pid(self):
        activation = (SCRIPT.parents[1] / "home/modules/activation/opencode.nix").read_text()
        self.assertIn(
            'export OPENCODE_LOCAL_BROWSER_ACTIVATION_PID="$BASHPID"', activation
        )
        self.assertIn(
            '--activation-pid "$OPENCODE_LOCAL_BROWSER_ACTIVATION_PID")"', activation
        )
        self.assertIn(
            '--activation-pid "\'\'${OPENCODE_LOCAL_BROWSER_ACTIVATION_PID:',
            activation,
        )

    def assert_targets_match(self,generation,files):
        for kind,root,path,source in SYNC.OUTPUTS:
            target=(self.config if root=="config" else self.data)/path
            if kind=="file":
                self.assertEqual(target.read_bytes(),files[source])
                self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o600)
            else:
                self.assertTrue(target.is_symlink())
                expected=self.data/"opencode-local"/"agent-browser"/"generations"/generation/source
                self.assertEqual(os.readlink(target),str(expected))

    def _make_generation(self, files, select=True):
        entries=[]
        for path,data in sorted(files.items()):
            entries.append({
                "path":path,
                "gitMode":"100644",
                "sourceGitBlobOid":"0"*40,
                "sha256":hashlib.sha256(data).hexdigest(),
                "size":len(data),
                "privateMode":"0600",
            })
        canonical=b"".join(x["path"].encode()+b"\0"+x["gitMode"].encode()+b"\0"+x["sha256"].encode()+b"\n" for x in entries)
        generation=hashlib.sha256(canonical).hexdigest()
        root=self.data/"opencode-local"/"agent-browser"
        gen=root/"generations"/generation
        for directory in (root,root/"generations",gen):
            directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        for rel,data in files.items():
            target=gen/rel
            target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            target.write_bytes(data)
            os.chmod(target,0o600)
        manifest={"schema":2,"objectFormat":"sha1","generation":generation,"files":entries}
        raw=(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode()
        (gen/"manifest.json").write_bytes(raw)
        os.chmod(gen/"manifest.json",0o600)
        if select:
            selector={"schema":1,"generation":generation,"manifestSha256":hashlib.sha256(raw).hexdigest()}
            (root/"current.json").write_text(json.dumps(selector,sort_keys=True,separators=(",",":"))+"\n")
            os.chmod(root/"current.json",0o600)
        return generation

    def select_generation(self,generation,previous=None):
        root=self.data/"opencode-local"/"agent-browser"
        manifest=(root/"generations"/generation/"manifest.json").read_bytes()
        selector={"schema":1,"generation":generation,"manifestSha256":hashlib.sha256(manifest).hexdigest()}
        if previous: selector["previousGeneration"]=previous
        current=root/"current.json"
        current.write_text(json.dumps(selector,sort_keys=True,separators=(",",":"))+"\n")
        os.chmod(current,0o600)

    def test_fresh_host_skips_when_no_private_source_exists(self):
        (self.data/"opencode-local"/"agent-browser"/"current.json").unlink()
        for path in SYNC._output_map(str(self.home),str(self.config),str(self.data),"0"*64):
            self.assertFalse((self.config if path["root"]=="config" else self.data).joinpath(path["path"]).exists())
        args=self.args
        self.assertEqual(SYNC._prepare(args,process_probe=lambda *a:[]),"skip")
        self.assertFalse((self.home/".local/state/opencode/agent-browser/deploy-pending").exists())

    def test_prepare_and_deploy_publish_only_verified_generation(self):
        transaction=SYNC._prepare(self.args,process_probe=lambda *a:[])
        self.args.transaction=transaction
        SYNC._deploy(self.args,process_probe=lambda *a:[])
        for kind,root,path,source in SYNC.OUTPUTS:
            target=(self.config if root=="config" else self.data)/path
            if kind=="file":
                self.assertEqual(target.read_bytes(),self.files[source])
                self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o600)
            else:
                self.assertTrue(target.is_symlink())
                self.assertEqual(os.readlink(target),str(self.data/"opencode-local/agent-browser/generations"/self.generation/source))
        self.assertFalse((self.home/".local/state/opencode/agent-browser/deploy-pending").exists())

    def test_newer_private_selection_survives_stale_activation_recovery(self):
        transaction=SYNC._prepare(self.args,process_probe=self.process_probe)
        new_files={name:("newer:"+name).encode() for name in SYNC.SOURCE_FILES}
        newer_generation=self._make_generation(new_files,select=False)
        self.select_generation(newer_generation)

        marker_path=self.home/".local/state/opencode/agent-browser/deploy-pending"
        marker=json.loads(marker_path.read_text())
        marker["activationPid"]=99999999
        marker["activationStart"]="not-running"
        marker_path.write_text(json.dumps(marker,sort_keys=True,separators=(",",":"))+"\n")
        os.chmod(marker_path,0o600)

        self.args.transaction=SYNC._prepare(self.args,process_probe=self.process_probe)
        self.assertNotEqual(self.args.transaction,transaction)
        selected=json.loads((self.data/"opencode-local/agent-browser/current.json").read_text())
        self.assertEqual(selected["generation"],newer_generation)
        SYNC._deploy(self.args,process_probe=self.process_probe)
        self.assert_targets_match(newer_generation,new_files)

    def test_first_migration_checks_existing_nix_store_links(self):
        targets=[]
        for spec in SYNC._output_map(str(self.home),str(self.config),str(self.data),self.generation):
            if spec["kind"] in ("dirlink","filelink"):
                root=self.config if spec["root"]=="config" else self.data
                target=root/spec["path"]
                target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                target.symlink_to("/nix/store/verified-browser-output")
                targets.append(target)

        with patch.object(SYNC,"_verify_nix_target",return_value=True) as verify:
            transaction=SYNC._prepare(self.args,process_probe=self.process_probe)

        self.assertNotEqual(transaction,"skip")
        self.assertGreaterEqual(verify.call_count,len(targets))

    def test_first_migration_validates_previous_generation(self):
        previous=self.generation
        new_files={name:("updated:"+name).encode() for name in SYNC.SOURCE_FILES}
        target_generation=self._make_generation(new_files,select=False)
        home,home_fd=SYNC._check_home(str(self.home))
        try:
            SYNC._install_generation(home_fd,home,str(self.config),str(self.data),previous,self.files,[(previous,self.files)])
        finally:
            os.close(home_fd)
        self.select_generation(target_generation,previous=previous)
        transaction=SYNC._prepare(self.args,process_probe=self.process_probe)
        self.args.transaction=transaction
        SYNC._deploy(self.args,process_probe=self.process_probe)
        self.assert_targets_match(target_generation,new_files)

    def test_unknown_destination_fails_before_marker(self):
        target=self.config/"opencode/tools/agent-browser.ts"
        target.parent.mkdir(parents=True,mode=0o700)
        target.write_text("user data\n")
        with self.assertRaises(SYNC.SyncError):
            SYNC._prepare(self.args,process_probe=lambda *a:[])
        self.assertEqual(target.read_text(),"user data\n")
        self.assertFalse((self.home/".local/state/opencode/agent-browser/deploy-pending").exists())

    def test_wrong_transaction_cannot_deploy(self):
        transaction=SYNC._prepare(self.args,process_probe=lambda *a:[])
        self.args.transaction="wrong-transaction"
        with self.assertRaises(SYNC.SyncError):
            SYNC._deploy(self.args,process_probe=lambda *a:[])
        marker=json.loads((self.home/".local/state/opencode/agent-browser/deploy-pending").read_text())
        self.assertEqual(marker["transaction"],transaction)
        self.args.transaction=transaction
        SYNC._deploy(self.args,process_probe=lambda *a:[])

    def test_stale_marker_recovers_from_immutable_generation(self):
        state=self.home/".local"/"state"/"opencode"/"agent-browser"
        state.mkdir(mode=0o700,parents=True)
        os.chmod(state,0o700)
        manifest_path=self.data/"opencode-local"/"agent-browser"/"generations"/self.generation/"manifest.json"
        marker={"schema":1,"transaction":"stale-transaction","activationPid":99999999,"activationStart":"not-running","previousGeneration":None,"targetGeneration":self.generation,"targetManifestSha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),"phase":"deploying"}
        (state/"deploy-pending").write_text(json.dumps(marker))
        os.chmod(state/"deploy-pending",0o600)
        transaction=SYNC._prepare(self.args,process_probe=self.process_probe)
        self.assertNotEqual(transaction,"stale-transaction")
        self.assert_targets_match(self.generation,self.files)
        self.args.transaction=transaction
        SYNC._deploy(self.args,process_probe=self.process_probe)

    def test_source_checksum_mismatch_fails_closed(self):
        target=self.data/"opencode-local/agent-browser/generations"/self.generation/next(iter(SYNC.SOURCE_FILES))
        target.write_text("tampered\n")
        with self.assertRaises(SYNC.SyncError):
            SYNC._prepare(self.args,process_probe=lambda *a:[])
        self.assertFalse((self.home/".local/state/opencode/agent-browser/deploy-pending").exists())


if __name__=="__main__":
    unittest.main()
