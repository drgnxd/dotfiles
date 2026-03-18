{ ... }:

{
  xdg.configFile = {
    "nushell/config.nu".source = ../../dot_config/nushell/config.nu;
    "nushell/env.nu".source = ../../dot_config/nushell/env.nu;
    "nushell/autoload/00-constants.nu".source = ../../dot_config/nushell/autoload/00-constants.nu;
    "nushell/autoload/00-helpers.nu".source = ../../dot_config/nushell/autoload/00-helpers.nu;
    "nushell/autoload/01-env.nu".source = ../../dot_config/nushell/autoload/01-env.nu;
    "nushell/autoload/02-path.nu".source = ../../dot_config/nushell/autoload/02-path.nu;
    "nushell/autoload/03-aliases.nu".source = ../../dot_config/nushell/autoload/03-aliases.nu;
    "nushell/autoload/04-functions.nu".source = ../../dot_config/nushell/autoload/04-functions.nu;
    "nushell/autoload/05-completions.nu".source = ../../dot_config/nushell/autoload/05-completions.nu;
    "nushell/autoload/06-integrations.nu".source = ../../dot_config/nushell/autoload/06-integrations.nu;
    "nushell/autoload/07-abbreviations.nu".source =
      ../../dot_config/nushell/autoload/07-abbreviations.nu;
    "nushell/autoload/10-source-tools.nu".source = ../../dot_config/nushell/autoload/10-source-tools.nu;
    "nushell/autoload/08-taskwarrior.nu".source = ../../dot_config/nushell/autoload/08-taskwarrior.nu;
    "nushell/autoload/09-lima.nu".source = ../../dot_config/nushell/autoload/09-lima.nu;
    "nushell/modules/integrations.nu".source = ../../dot_config/nushell/modules/integrations.nu;
    "nushell/modules/taskwarrior.nu".source = ../../dot_config/nushell/modules/taskwarrior.nu;
    "nushell/modules/lima.nu".source = ../../dot_config/nushell/modules/lima.nu;
  };
}
