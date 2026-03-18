_:

let
  src = ../../dot_config/taskwarrior;
in
{
  xdg.configFile = {
    "taskwarrior/config".source = "${src}/config";
    "taskwarrior/colors.rc".source = "${src}/colors.rc";
    "taskwarrior/reports.rc".source = "${src}/reports.rc";
    "taskwarrior/CACHE_ARCHITECTURE.md".source = "${src}/CACHE_ARCHITECTURE.md";

    "taskwarrior/hooks/on-add.py" = {
      source = "${src}/hooks/on-add.py";
      executable = true;
    };
    "taskwarrior/hooks/on-modify.py" = {
      source = "${src}/hooks/on-modify.py";
      executable = true;
    };
    "taskwarrior/hooks/hook_entrypoint.py".source = "${src}/hooks/hook_entrypoint.py";
    "taskwarrior/hooks/update_cache.py" = {
      source = "${src}/hooks/update_cache.py";
      executable = true;
    };
  };
}
