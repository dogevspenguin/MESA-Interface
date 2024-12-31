import tkinter as tk

from tkinter import *
from tkinter import ttk, messagebox,filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mesa_web import find_read_profile
from mesa_web import read_history
import sys
import json
from matplotlib.animation import FuncAnimation
import numpy as np
animation_paused = False
def create_gui(filename):
    # Load data using read_history
    data = read_history(filename)
    
    # Extract column names
    column_names = list(data.keys())

    # Tkinter window setup
    window = tk.Tk()
    window.title("MESA Visualization")
    window.geometry("1200x800")

    # Create the Notebook (tabbed interface)
    notebook = ttk.Notebook(window)
    notebook.pack(fill="both", expand=True)

    # Tab 1: History tab
    history_tab = ttk.Frame(notebook)
    notebook.add(history_tab, text="History")

    # Tab 2: Profile tab
    profile_tab = ttk.Frame(notebook)
    notebook.add(profile_tab, text="Profile")

    def create_history_tab():
        # Dropdown for selecting x-axis
        tk.Label(history_tab, text="Select X Axis:").pack(pady=5)
        x_dropdown = ttk.Combobox(history_tab, values=column_names)
        x_dropdown.set(column_names[0])
        x_dropdown.pack()

        # Dropdown for selecting y-axis
        tk.Label(history_tab, text="Select Y Axis:").pack(pady=5)
        y_dropdown = ttk.Combobox(history_tab, values=column_names)
        y_dropdown.set(column_names[1])
        y_dropdown.pack()

        # Dropdown for selecting color
        tk.Label(history_tab, text="Select Plot Color:").pack(pady=5)
        colors = ["blue", "red", "green", "orange", "purple", "black"]
        color_dropdown = ttk.Combobox(history_tab, values=colors)
        color_dropdown.set("blue")
        color_dropdown.pack()

        # Checkbuttons to flip axes
        x_flip_var = tk.BooleanVar()
        y_flip_var = tk.BooleanVar()
        
        tk.Checkbutton(history_tab, text="Flip X Axis", variable=x_flip_var).pack(pady=5)
        tk.Checkbutton(history_tab, text="Flip Y Axis", variable=y_flip_var).pack(pady=5)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.grid(True)

        def on_plot_button_click():
            x_col = x_dropdown.get()
            y_col = y_dropdown.get()
            plot_color = color_dropdown.get()

            try:
                x_values = data[x_col]
                y_values = data[y_col]

                if len(x_values) != len(y_values):
                    return

                ax.plot(x_values, y_values, color=plot_color)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title(f"{y_col} vs {x_col}")

                if x_flip_var.get():
                    ax.invert_xaxis()
                if y_flip_var.get():
                    ax.invert_yaxis()

                canvas.draw()

            except KeyError:
                print("ERROR in plotting")

        def plot_and_clear():
            ax.clear()
            on_plot_button_click()
        
        def on_add_plot_button_click():
            on_plot_button_click()

        tk.Button(history_tab, text="Plot Data", command=plot_and_clear).pack(pady=10)
        tk.Button(history_tab, text="Add Another Plot", command=on_add_plot_button_click).pack(pady=10)

        canvas = FigureCanvasTkAgg(fig, master=history_tab)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, history_tab)
        toolbar.update()
        toolbar.pack()

        canvas.get_tk_widget().pack()

    def create_profile_tab(target_mn):
        available_properties = list(find_read_profile("profiles.index", 1).keys())
        plot_configs = []

        # Create main frame for profile controls
        controls_frame = ttk.Frame(profile_tab)
        controls_frame.pack(fill="x", padx=10, pady=5)
        container = ttk.Frame(profile_tab)
        container.pack(fill="x", expand=True, padx=10, pady=5)
        # Create canvas for scrollable area with fixed height
        scrollable_frame = ttk.Frame(container)
        scrollable_frame.pack(fill="x", expand=True)
        config_canvas = tk.Canvas(scrollable_frame, height=200)
        config_canvas.pack(side="left", fill="x", expand=True)
        # Create a vertical scrollbar and link it to the canvas
        vertical_scrollbar = ttk.Scrollbar(scrollable_frame, orient="vertical", command=config_canvas.yview)
        vertical_scrollbar.pack(side="right", fill="y")

        # Configure the canvas to update the scrollbar
        config_canvas.configure(yscrollcommand=vertical_scrollbar.set)

        # Create a frame inside the canvas to hold your widgets
        plots_frame = ttk.Frame(config_canvas)

        # Add the frame to the canvas window
        config_canvas.create_window((0, 0), window=plots_frame, anchor="nw")
        def configure_scroll_region(event):
            config_canvas.configure(scrollregion=config_canvas.bbox("all"))
        def on_mousewheel(event):
            config_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        config_canvas.bind_all("<MouseWheel>", on_mousewheel)
        plots_frame.bind("<Configure>", configure_scroll_region)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.grid(True)
        def get_profile_data(mn):
            return find_read_profile("profiles.index", mn)
        def save_plot_config(name_var, plot_configs):
            file_name = f"{name_var}.pltbin"
            try:
                # Convert the plot_configs to a JSON-friendly format
                json_friendly_configs = []
                for config in plot_configs:
                    json_friendly_configs.append({
                        'x_dropdown': config['x_dropdown'].get(),
                        'y_dropdown': config['y_dropdown'].get(),
                        'color_dropdown': config['color_dropdown'].get(),
                        'x_log_var': config['x_log_var'].get(),
                        'y_log_var': config['y_log_var'].get(),
                        'x_min_entry': config['x_min_entry'].get(),
                        'x_max_entry': config['x_max_entry'].get(),
                        'y_min_entry': config['y_min_entry'].get(),
                        'y_max_entry': config['y_max_entry'].get(),
                    })

                # Save to a JSON file
                with open(file_name, 'w') as file:
                    json.dump(json_friendly_configs, file, indent=4)
                print(f"Plot configurations saved successfully to {file_name}.")
            except Exception as e:
                print(f"An error occurred while saving the plot configurations: {e}")

        def load_plot_configurations(file_name):
            try:
                with open(file_name, 'r') as file:
                    saved_configs = json.load(file)  # Load the saved configurations

                for config in saved_configs:
                    # Create a new plot configuration and populate its fields
                    try:
                        add_loaded_plot_configuration(
                            config['x_dropdown'], 
                            config['y_dropdown'], 
                            config['color_dropdown'], 
                            config['x_log_var'], 
                            config['y_log_var'], 
                            config['x_min_entry'], 
                            config['x_max_entry'], 
                            config['y_min_entry'], 
                            config['y_max_entry']
                        )
                        if not available_properties.index(config['x_dropdown']):
                            print(f"Error loading {config['x_dropdown']} property does not exist")
                        if not available_properties.index(config['y_dropdown']):
                            print(f"Error loading {config['y_dropdown']} property does not exist")
                    except Exception as e:
                        print(f"Error loading {config['x_dropdown'], config['y_dropdown'], config['color_dropdown'], config['x_log_var'], config['y_log_var'], config['x_min_entry'], config['x_max_entry'], config['y_min_entry'], config['y_max_entry']}")
                print(f"Plot configurations loaded successfully from {file_name}.")
            except Exception as e:
                print(f"An error occurred while loading the plot configurations: {e}")
        def open_file_dialog():
            file_name = filedialog.askopenfilename(
                title="Open Plot Configuration File",
                filetypes=[("Plot Configuration Files", "*.pltbin"), ("All Files", "*.*")]
            )
            if file_name:
                load_plot_configurations(file_name)
        def add_plot_configuration():
            config_frame = ttk.Frame(plots_frame)
            config_frame.pack(pady=5, fill="x")

            x_dropdown = ttk.Combobox(config_frame, values=available_properties, width=20)
            x_dropdown.set(available_properties[0])
            x_dropdown.grid(row=0, column=0, padx=5, pady=5)

            y_dropdown = ttk.Combobox(config_frame, values=available_properties, width=20)
            y_dropdown.set(available_properties[1])
            y_dropdown.grid(row=0, column=1, padx=5, pady=5)

            color_dropdown = ttk.Combobox(config_frame, values=["blue", "green", "red", "cyan", "magenta", "yellow", "black"], width=15)
            color_dropdown.set("blue")
            color_dropdown.grid(row=0, column=2, padx=5, pady=5)

            x_log_var = tk.BooleanVar()
            y_log_var = tk.BooleanVar()
            
            x_log_checkbox = ttk.Checkbutton(config_frame, text="Log X", variable=x_log_var)
            x_log_checkbox.grid(row=0, column=3, padx=5, pady=5)

            y_log_checkbox = ttk.Checkbutton(config_frame, text="Log Y", variable=y_log_var)
            y_log_checkbox.grid(row=0, column=4, padx=5, pady=5)

            x_min_entry = ttk.Entry(config_frame, width=10)
            x_min_entry.insert(0, "MinX")
            x_min_entry.grid(row=1, column=0, padx=5, pady=5)

            x_max_entry = ttk.Entry(config_frame, width=10)
            x_max_entry.insert(0, "MaxX")
            x_max_entry.grid(row=1, column=1, padx=5, pady=5)

            y_min_entry = ttk.Entry(config_frame, width=10)
            y_min_entry.insert(0, "MinY")
            y_min_entry.grid(row=1, column=2, padx=5, pady=5)

            y_max_entry = ttk.Entry(config_frame, width=10)
            y_max_entry.insert(0, "MaxY")
            y_max_entry.grid(row=1, column=3, padx=5, pady=5)

            plot_config = {
                'frame': config_frame,
                'x_dropdown': x_dropdown,
                'y_dropdown': y_dropdown,
                'color_dropdown': color_dropdown,
                'x_log_var': x_log_var,
                'y_log_var': y_log_var,
                'x_min_entry': x_min_entry,
                'x_max_entry': x_max_entry,
                'y_min_entry': y_min_entry,
                'y_max_entry': y_max_entry
            }

            def remove_plot():
                plot_configs.remove(plot_config)
                config_frame.destroy()
                config_canvas.configure(scrollregion=config_canvas.bbox("all"))

            remove_button = ttk.Button(config_frame, text="Remove", command=remove_plot)
            remove_button.grid(row=1, column=4, padx=5, pady=5)
            config_canvas.configure(scrollregion=config_canvas.bbox("all"))
            plot_configs.append(plot_config)
        def add_loaded_plot_configuration(x_value, y_value, color, x_log, y_log, x_min, x_max, y_min, y_max):
            config_frame = ttk.Frame(plots_frame)
            config_frame.pack(pady=5, fill="x")

            x_dropdown = ttk.Combobox(config_frame, values=available_properties, width=20)
            x_dropdown.set(x_value)  # Set the loaded value
            x_dropdown.grid(row=0, column=0, padx=5, pady=5)

            y_dropdown = ttk.Combobox(config_frame, values=available_properties, width=20)
            y_dropdown.set(y_value)  # Set the loaded value
            y_dropdown.grid(row=0, column=1, padx=5, pady=5)

            color_dropdown = ttk.Combobox(config_frame, values=["blue", "green", "red", "cyan", "magenta", "yellow", "black"], width=15)
            color_dropdown.set(color)  # Set the loaded value
            color_dropdown.grid(row=0, column=2, padx=5, pady=5)

            x_log_var = tk.BooleanVar(value=x_log)  # Set the loaded value
            y_log_var = tk.BooleanVar(value=y_log)  # Set the loaded value

            x_log_checkbox = ttk.Checkbutton(config_frame, text="Log X", variable=x_log_var)
            x_log_checkbox.grid(row=0, column=3, padx=5, pady=5)

            y_log_checkbox = ttk.Checkbutton(config_frame, text="Log Y", variable=y_log_var)
            y_log_checkbox.grid(row=0, column=4, padx=5, pady=5)

            x_min_entry = ttk.Entry(config_frame, width=10)
            x_min_entry.insert(0, x_min)  # Set the loaded value
            x_min_entry.grid(row=1, column=0, padx=5, pady=5)

            x_max_entry = ttk.Entry(config_frame, width=10)
            x_max_entry.insert(0, x_max)  # Set the loaded value
            x_max_entry.grid(row=1, column=1, padx=5, pady=5)

            y_min_entry = ttk.Entry(config_frame, width=10)
            y_min_entry.insert(0, y_min)  # Set the loaded value
            y_min_entry.grid(row=1, column=2, padx=5, pady=5)

            y_max_entry = ttk.Entry(config_frame, width=10)
            y_max_entry.insert(0, y_max)  # Set the loaded value
            y_max_entry.grid(row=1, column=3, padx=5, pady=5)

            plot_config = {
                'frame': config_frame,
                'x_dropdown': x_dropdown,
                'y_dropdown': y_dropdown,
                'color_dropdown': color_dropdown,
                'x_log_var': x_log_var,
                'y_log_var': y_log_var,
                'x_min_entry': x_min_entry,
                'x_max_entry': x_max_entry,
                'y_min_entry': y_min_entry,
                'y_max_entry': y_max_entry
            }

            def remove_plot():
                plot_configs.remove(plot_config)
                config_frame.destroy()
                config_canvas.configure(scrollregion=config_canvas.bbox("all"))
            remove_button = ttk.Button(config_frame, text="Remove", command=remove_plot)
            remove_button.grid(row=1, column=4, padx=5, pady=5)
            config_canvas.configure(scrollregion=config_canvas.bbox("all"))
            plot_configs.append(plot_config)


        
        plotname = ttk.Entry(controls_frame, width=10)
        plotname.insert(0, "Plot name")
        plotname.pack(side="right",padx=5)

        open_file_button = ttk.Button(controls_frame, text="Open File", command=open_file_dialog)
        open_file_button.pack(pady=10)

        add_plot_button = tk.Button(controls_frame, text="Add Plot", command=add_plot_configuration)
        add_plot_button.pack(side="left", padx=5)
        save_plot_button = tk.Button(
            controls_frame,
            text="Save Plot",
            command=lambda: save_plot_config(plotname.get(), plot_configs)
        )
        save_plot_button.pack(side="left", padx=5)
        
        speed_slider = tk.Scale(controls_frame, from_=0, to=1000, orient="horizontal", label="Speed (mn/s)")
        speed_slider.set(1)
        speed_slider.pack(side="left", padx=20)

        def animate_profile(frame):
            mn = frame*speed_slider.get()
            if mn > target_mn:
                return
                
            data = get_profile_data(mn)
            ax.clear()
            ax.grid(True)

            for config in plot_configs:
                try:
                    selected_x = config['x_dropdown'].get()
                    selected_y = config['y_dropdown'].get()
                    color = config['color_dropdown'].get()
                    use_log_x = config['x_log_var'].get()
                    use_log_y = config['y_log_var'].get()

                    x_min_entry = config['x_min_entry'].get()
                    x_max_entry = config['x_max_entry'].get()
                    y_min_entry = config['y_min_entry'].get()
                    y_max_entry = config['y_max_entry'].get()
                    if selected_x not in data or selected_y not in data:
                        continue

                    x_values = data[selected_x]
                    y_values = data[selected_y]

                    if len(x_values) != len(y_values):
                        continue

                    try:
                        x_min = float(x_min_entry)
                        x_max = float(x_max_entry)
                        y_min = float(y_min_entry)
                        y_max = float(y_max_entry)

                        adjusted_x_values = []
                        adjusted_y_values = []
                        for x, y in zip(x_values, y_values):
                            if x < x_min:
                                x = x_min
                            elif x > x_max:
                                x = x_max

                            if y < y_min:
                                y = y_min
                            elif y > y_max:
                                y = y_max

                            adjusted_x_values.append(x)
                            adjusted_y_values.append(y)

                        x_values = adjusted_x_values
                        y_values = adjusted_y_values
                    except ValueError:
                        pass  # Ignore invalid bounds

                    if use_log_x:
                        ax.set_xscale("log")
                    if use_log_y:
                        ax.set_yscale("log")

                    ax.plot(x_values, y_values, label=f"{selected_y} vs {selected_x} at mn={mn}", color=color)
                except Exception as e:
                    print(f"Error plotting: {e}")

            ax.legend()
            canvas.draw_idle()

        animation = None

        def start_animation():
            nonlocal animation
            if animation is None:
                animation = FuncAnimation(fig, animate_profile, frames=range(0, target_mn + 1), repeat=False)
                animation.event_source.start()
                # Pure black magic to fix ui not updating
                current_width = window.winfo_width()
                current_height = window.winfo_height()
                current_x = window.winfo_x()
                current_y = window.winfo_y()
                new_width = current_width - 1
                window.geometry(f"{new_width}x{current_height}+{current_x}+{current_y}")
                current_width = window.winfo_width()
                current_height = window.winfo_height()
                current_x = window.winfo_x()
                current_y = window.winfo_y()
                new_width = current_width + 1
                window.geometry(f"{new_width}x{current_height}+{current_x}+{current_y}")
            else:
                animation.event_source.stop()
                animation = None
                animation = FuncAnimation(fig, animate_profile, frames=range(0, target_mn + 1), repeat=False)
                animation.event_source.start()
                # Pure black magic to fix ui not updating
                current_width = window.winfo_width()
                current_height = window.winfo_height()
                current_x = window.winfo_x()
                current_y = window.winfo_y()
                new_width = current_width - 1
                window.geometry(f"{new_width}x{current_height}+{current_x}+{current_y}")
                current_width = window.winfo_width()
                current_height = window.winfo_height()
                current_x = window.winfo_x()
                current_y = window.winfo_y()
                new_width = current_width + 1
                window.geometry(f"{new_width}x{current_height}+{current_x}+{current_y}")
        def pause_animation():
            global animation_paused
            if animation_paused:
                animation.resume()
                Pause_button.config(text="Pause Animation")
            else:
                animation.pause()
                Pause_button.config(text="Unpause Animation")
            animation_paused = not animation_paused
        Pause_button = tk.Button(controls_frame, text="Pause Animation", command=pause_animation)
        Pause_button.pack(side="left", padx=5)
        start_button = tk.Button(controls_frame, text="Start Animation", command=start_animation)
        start_button.pack(side="left", padx=5)

        canvas = FigureCanvasTkAgg(fig, master=profile_tab)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, profile_tab)
        toolbar.update()
        toolbar.pack()

        canvas.get_tk_widget().pack(fill="both", expand=True)
    create_history_tab()
    create_profile_tab(target_mn=17000)

    def on_closing():
        window.quit()
        sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    window.mainloop()

if __name__ == "__main__":
    filename = "history.data"
    create_gui(filename)