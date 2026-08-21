_:

{
  programs.btop = {
    enable = true;
    settings = {
      color_theme = "Default";
      theme_background = true;
      truecolor = true;
      rounded_corners = true;
      terminal_sync = true;
      graph_symbol = "braille";
      shown_boxes = "cpu mem net proc";
      update_ms = 2000;
      proc_sorting = "cpu lazy";
      proc_colors = true;
      proc_gradient = true;
      proc_mem_bytes = true;
      show_uptime = true;
      show_cpu_freq = true;
      temp_scale = "celsius";
      mem_graphs = true;
      show_swap = true;
      show_disks = true;
      only_physical = true;
      show_io_stat = true;
      show_battery = true;
      log_level = "WARNING";
      # Generated settings are immutable Nix-store links.
      save_config_on_exit = false;
    };
  };
}
