"""
VoxBridge GUI Application
Cross-platform GUI using tkinter
"""

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import queue
from typing import Optional

# Import VoxBridge components
try:
    from ..converter import VoxBridgeConverter, InputValidationError, ConversionError, BlenderNotFoundError
    from .. import __version__
    VOXBRIDGE_AVAILABLE = True
except ImportError:
    VOXBRIDGE_AVAILABLE = False
    __version__ = "1.0.0"


class VoxBridgeGUI:
    """Main GUI application for VoxBridge"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"VoxBridge v{__version__} - VoxEdit to Unity/Roblox Converter")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Initialize converter
        self.converter = VoxBridgeConverter() if VOXBRIDGE_AVAILABLE else None
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        self.setup_ui()
        self.setup_styles()
        
        # Start message processing
        self.process_messages()
    
    def setup_styles(self):
        """Setup modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="VoxBridge", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="VoxEdit to Unity/Roblox Converter", style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Input file selection
        ttk.Label(main_frame, text="Input Files:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=50)
        input_entry.grid(row=2, column=1, sticky="ew", padx=(5, 5), pady=5)
        input_buttons_frame = ttk.Frame(main_frame)
        input_buttons_frame.grid(row=2, column=2, pady=5)
        ttk.Button(input_buttons_frame, text="Single File", command=self.browse_input).pack(side=tk.TOP, pady=2)
        ttk.Button(input_buttons_frame, text="Batch Files", command=self.browse_batch_input).pack(side=tk.TOP, pady=2)
        
        # Output folder selection
        ttk.Label(main_frame, text="Output Folder:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=50)
        output_entry.grid(row=3, column=1, sticky="ew", padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output_folder).grid(row=3, column=2, pady=5)
        
        # Target platform
        ttk.Label(main_frame, text="Target Platform:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.target_var = tk.StringVar(value="unity")
        target_combo = ttk.Combobox(main_frame, textvariable=self.target_var, values=["unity", "roblox"], state="readonly", width=15)
        target_combo.grid(row=4, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Conversion Options", padding="10")
        options_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        
        # Checkboxes
        self.optimize_mesh_var = tk.BooleanVar()
        self.generate_atlas_var = tk.BooleanVar()
        self.compress_textures_var = tk.BooleanVar()
        self.no_blender_var = tk.BooleanVar()
        self.report_var = tk.BooleanVar()
        self.verbose_var = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="Optimize Mesh", variable=self.optimize_mesh_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Generate Atlas", variable=self.generate_atlas_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Compress Textures", variable=self.compress_textures_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="No Blender", variable=self.no_blender_var).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Generate Report", variable=self.report_var).grid(row=2, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Verbose Output", variable=self.verbose_var).grid(row=2, column=1, sticky=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        ttk.Button(buttons_frame, text="Convert", command=self.start_conversion).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="System Check", command=self.run_system_check).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Clear", command=self.clear_form).pack(side=tk.LEFT)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=8, width=70)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure main frame weights
        main_frame.rowconfigure(8, weight=1)
    
    def browse_input(self):
        """Browse for input file"""
        filetypes = [
            ("glTF files", "*.gltf"),
            ("GLB files", "*.glb"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=filetypes
        )
        if filename:
            self.input_var.set(filename)
            # Auto-generate output filename
            input_path = Path(filename)
            target = self.target_var.get()
            output_path = input_path.parent / f"{input_path.stem}_{target}_clean{input_path.suffix}"
            self.output_var.set(str(output_path))
    
    def browse_output(self):
        """Browse for output file (legacy method)"""
        filetypes = [
            ("glTF files", "*.gltf"),
            ("GLB files", "*.glb"),
            ("All files", "*.*")
        ]
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            filetypes=filetypes,
            defaultextension=".glb"
        )
        if filename:
            self.output_var.set(filename)
    
    def browse_batch_input(self):
        """Browse for multiple input files"""
        filetypes = [
            ("GLB files", "*.glb"),
            ("glTF files", "*.gltf"),
            ("All files", "*.*")
        ]
        filenames = filedialog.askopenfilenames(
            title="Select Input Files (Batch Mode)",
            filetypes=filetypes
        )
        if filenames:
            # Join multiple files with semicolon for display
            self.input_var.set("; ".join(filenames))
            # Auto-generate output folder name
            if len(filenames) > 1:
                input_dir = Path(filenames[0]).parent
                target = self.target_var.get()
                output_folder = input_dir / f"voxbridge_output_{target}"
                self.output_var.set(str(output_folder))
    
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(
            title="Select Output Folder"
        )
        if folder:
            self.output_var.set(folder)
    
    def log_message(self, message: str, level: str = "info"):
        """Add message to log"""
        self.message_queue.put(("log", message, level))
    
    def update_progress(self, message: str):
        """Update progress message"""
        self.message_queue.put(("progress", message))
    
    def process_messages(self):
        """Process messages from queue"""
        try:
            while True:
                msg_type, *args = self.message_queue.get_nowait()
                
                if msg_type == "log":
                    message, level = args
                    self.log_text.insert(tk.END, f"[{level.upper()}] {message}\n")
                    self.log_text.see(tk.END)
                elif msg_type == "progress":
                    message = args[0]
                    self.progress_var.set(message)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        if not self.validate_inputs():
            return
        
        # Disable convert button during processing
        self.convert_button = self.root.focus_get()
        
        # Start conversion in separate thread
        thread = threading.Thread(target=self.run_conversion, daemon=True)
        thread.start()
    
    def validate_inputs(self) -> bool:
        """Validate user inputs"""
        input_files_str = self.input_var.get().strip()
        output_folder = self.output_var.get().strip()
        target = self.target_var.get()
        
        if not input_files_str:
            messagebox.showerror("Error", "Please select input file(s).")
            return False
        
        if not output_folder:
            messagebox.showerror("Error", "Please specify an output folder.")
            return False
        
        # Parse input files (support both single and batch)
        if ";" in input_files_str:
            # Batch mode - multiple files separated by semicolon
            input_files = [Path(f.strip()) for f in input_files_str.split(";")]
        else:
            # Single file mode
            input_files = [Path(input_files_str)]
        
        # Validate each input file
        for input_path in input_files:
            if not input_path.exists():
                messagebox.showerror("Error", f"Input file does not exist: {input_path}")
                return False
            if input_path.suffix.lower() not in ['.glb', '.gltf']:
                messagebox.showerror("Error", f"Input file must be .glb or .gltf: {input_path}")
                return False
        
        # Validate output folder
        output_path = Path(output_folder)
        if not output_path.exists():
            # Try to create the folder
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output folder: {e}")
                return False
        
        if target not in ["unity", "roblox"]:
            messagebox.showerror("Error", "Target must be 'unity' or 'roblox'")
            return False
        
        # Store input files for conversion
        self.input_files = input_files
        self.output_folder = output_path
        
        return True
    
    def run_conversion(self):
        """Run the conversion process"""
        try:
            self.update_progress("Starting conversion...")
            self.log_message("Starting VoxBridge conversion", "info")
            
            # Get parameters from validation
            input_files = getattr(self, 'input_files', [])
            output_folder = getattr(self, 'output_folder', None)
            target = self.target_var.get()
            
            if not input_files or not output_folder:
                self.log_message("Error: Input files or output folder not set", "error")
                return
            
            # Get options
            optimize_mesh = self.optimize_mesh_var.get()
            no_blender = self.no_blender_var.get()
            verbose = self.verbose_var.get()
            
            self.log_message(f"Input files: {len(input_files)}", "info")
            self.log_message(f"Output folder: {output_folder}", "info")
            self.log_message(f"Target: {target}", "info")
            
            # Run conversions
            if self.converter:
                successful_conversions = 0
                total_files = len(input_files)
                
                for i, input_file in enumerate(input_files, 1):
                    self.update_progress(f"Converting file {i} of {total_files}: {input_file.name}")
                    self.log_message(f"Converting {input_file.name}...", "info")
                    
                    # Generate output path for this file
                    output_file = output_folder / f"{input_file.stem}_{target}"
                    
                    try:
                        use_blender = not no_blender
                        success = self.converter.convert_file(
                            input_file, output_file, use_blender,
                            optimize_mesh=optimize_mesh,
                            platform=target
                        )
                        
                        if success:
                            successful_conversions += 1
                            self.log_message(f"✓ {input_file.name} converted successfully!", "success")
                            
                            # Check if ZIP was created
                            zip_path = output_file.with_suffix('.zip')
                            if zip_path.exists():
                                self.log_message(f"  → Packaged into {zip_path.name}", "info")
                            else:
                                self.log_message(f"  → Output saved as {output_file.with_suffix('.gltf').name}", "info")
                        else:
                            self.log_message(f"✗ {input_file.name} conversion failed!", "error")
                            
                    except Exception as e:
                        self.log_message(f"✗ Error converting {input_file.name}: {e}", "error")
                
                # Final summary
                if successful_conversions > 0:
                    self.update_progress(f"Conversion completed: {successful_conversions}/{total_files} files")
                    self.log_message(f"Conversion completed: {successful_conversions}/{total_files} files successfully!", "success")
                    
                    # Show completion message with output folder link
                    completion_msg = f"Conversion completed!\n\n{successful_conversions} of {total_files} files converted successfully.\n\nOutput folder: {output_folder}"
                    if successful_conversions == total_files:
                        messagebox.showinfo("Success", completion_msg)
                    else:
                        messagebox.showwarning("Partial Success", completion_msg)
                else:
                    self.update_progress("All conversions failed")
                    self.log_message("All conversions failed!", "error")
                    messagebox.showerror("Error", "All conversions failed. Check the log for details.")
            else:
                self.log_message("VoxBridge converter not available", "error")
                self.update_progress("Converter not available")
                messagebox.showerror("Error", "VoxBridge converter not available")
                
        except Exception as e:
            self.log_message(f"Error during conversion: {e}", "error")
            self.update_progress("Error occurred")
            messagebox.showerror("Error", f"Error during conversion: {e}")
    
    def run_system_check(self):
        """Run system diagnostics"""
        self.log_message("Running system diagnostics...", "info")
        
        # Check Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.log_message(f"Python version: {python_version}", "info")
        
        # Check VoxBridge availability
        if self.converter:
            self.log_message("VoxBridge converter: Available", "success")
        else:
            self.log_message("VoxBridge converter: Not available", "error")
        
        # Check Blender
        if self.converter:
            blender_path = self.converter.find_blender()
            if blender_path:
                self.log_message(f"Blender: Found at {blender_path}", "success")
            else:
                self.log_message("Blender: Not found", "warning")
        
        self.log_message("System check completed", "info")
    
    def clear_form(self):
        """Clear all form fields"""
        self.input_var.set("")
        self.output_var.set("")
        self.target_var.set("unity")
        self.optimize_mesh_var.set(False)
        self.generate_atlas_var.set(False)
        self.compress_textures_var.set(False)
        self.no_blender_var.set(False)
        self.report_var.set(False)
        self.verbose_var.set(False)
        self.progress_var.set("Ready")
        self.log_text.delete(1.0, tk.END)
        
        # Clear batch processing attributes
        if hasattr(self, 'input_files'):
            delattr(self, 'input_files')
        if hasattr(self, 'output_folder'):
            delattr(self, 'output_folder')


def run():
    """Run the VoxBridge GUI application"""
    try:
        # Create main window
        root = tk.Tk()
        
        # Create and run GUI
        app = VoxBridgeGUI(root)
        
        # Start the GUI event loop
        root.mainloop()
        
        return 0
    except Exception as e:
        print(f"GUI Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run()) 