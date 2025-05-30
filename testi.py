import tkinter as tk
from tkinter import filedialog, messagebox, Text, ttk
from abc import ABC, abstractmethod
import keyword
import re
import tkinter.font

# Defining syntax highlighting function
def syntax_highlight(text_widget: Text):
    # Remove previous tags for syntax highlighting
    text_widget.tag_remove("keyword", "1.0", "end")
    text_widget.tag_remove("string", "1.0", "end")
    text_widget.tag_remove("comment", "1.0", "end")

    # Get all text from the Text widget
    text_content = text_widget.get("1.0", "end-1c")

    # Highlight keywords in blue (only standalone words)
    lines = text_content.split("\n")
    for line_number, line in enumerate(lines, start=1):
        words = line.split()
        for word in words:
            if word in keyword.kwlist:  # Check if the word is a Python keyword
                start = f"{line_number}.{line.find(word)}"
                end = f"{start}+{len(word)}c"
                text_widget.tag_add("keyword", start, end)
    text_widget.tag_config("keyword", foreground="blue", font=("Arial", 10, "bold"))

    # Highlight strings in green
    start = "1.0"
    while True:
        start = text_widget.search(r'".*?"', start, stopindex="end", regexp=True)
        if not start:
            break
        end = f"{start}+{len(text_widget.get(start, f'{start} lineend'))}c"
        text_widget.tag_add("string", start, end)
        start = end
    text_widget.tag_config("string", foreground="green", font=("Arial", 10, "bold"))

    # Highlight comments in gray
    start = "1.0"
    while True:
        start = text_widget.search(r"#.*", start, stopindex="end", regexp=True)
        if not start:
            break
        line_end = start.split('.')[0] + '.end'
        text_widget.tag_add("comment", start, line_end)
        start = line_end
    text_widget.tag_config("comment", foreground="gray", font=("Arial", 10, "bold"))

# Autocomplete function for Python keywords
def autocomplete(event, text_widget: Text):
    typed_text = text_widget.get("insert-1c", "insert")  # Get last typed character

    # Finding the current word typed
    words = typed_text.split()
    if words:
        last_word = words[-1]

        # Finding matching keywords from keyword list
        matches = [kw for kw in keyword.kwlist if kw.startswith(last_word)]

        if matches:
            # The first match and replacing the current word with the complete keyword
            match = matches[0]
            start_pos = "insert-1c linestart"
            end_pos = "insert"
            text_widget.delete(start_pos, end_pos)  # Removing the incomplete word
            text_widget.insert("insert", match)  # Inserting the matching keyword

# Abstract class for Blocks defining the interface for all blocks(=buttons) for the ribbon
class Block(ttk.Frame, ABC):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

    @abstractmethod
    def disable(self, nro):
        pass

    def disableAll(self):
        for btn in self.buttons:
            btn.config(state="disabled")

    def enableAll(self):
        for btn in self.buttons:
            btn.config(state="normal")

class ButtonsRibbon(Block):
    def __init__(self, parent, NotesApp):
        super().__init__(parent)
        self.NotesApp = NotesApp
        
        self.undo_btn = tk.Button(self, text="UNDO", command=self.NotesApp.undo)
        self.redo_btn = tk.Button(self, text="REDO", command=self.NotesApp.redo)
        self.copy_btn = tk.Button(self, text="COPY", command=self.NotesApp.copy)
        self.paste_btn = tk.Button(self, text="PASTE", command=self.NotesApp.paste)
        self.close_btn = tk.Button(self, text="CLOSE", command=self.NotesApp.close)
        
        self.buttons = [self.undo_btn, self.redo_btn, self.copy_btn, self.paste_btn, self.close_btn]
        for btn in self.buttons:
            btn.pack(side=tk.LEFT)
    
    def disable(self, nro):
        if 0 <= nro < len(self.buttons):
            self.buttons[nro].config(state="disabled")
        
    def update_buttons(self):
        self.undo_btn.config(state="normal")
        self.redo_btn.config(state="normal")
        self.copy_btn.config(state="normal")
        self.paste_btn.config(state="normal")
        self.close_btn.config(state="normal")

# Tkinter Application
class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bestest Text Editor")
        self.maxsize(4096, 2400) # Setting the maximum size of the window
        self.minsize(400, 100) # Setting the minimum size of the window

        # Top Frame
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        # Menu Bar
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        self.config(menu=menu_bar)

        # Search Bar
        self.search_entry = tk.Entry(self.top_frame, width=20)
        self.search_entry.pack(side=tk.RIGHT, padx=5)
        self.search_button = tk.Button(self.top_frame, text="Search", command=self.search_word, bg="lightblue")
        self.search_button.pack(side=tk.RIGHT, padx=5)

        # Frame for line numbers and main text
        self.text_frame = tk.Frame(self)
        self.text_frame.pack(expand=True, fill=tk.BOTH)

        # Line number display
        self.line_numbers = tk.Text(self.text_frame, width=4, bg="#f0f0f0", state="disabled", wrap="none", font=("Arial", 10))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Text Area
        self.text_area = tk.Text(self.text_frame, wrap="word", undo=True, bg="#ffffff", highlightthickness=0, relief="flat", font=("Arial", 10))
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # Keyboard shortcuts
        self.bind_all("<Control-o>", lambda event: self.open_file()) # Keyboard shortcut for open
        self.bind_all("<Control-s>", lambda event: self.save_file()) # Keyboard shortcut for save
        self.bind_all("<Control-z>", lambda event: self.undo()) # Keyboard shortcut for undo
        self.bind_all("<Control-y>", lambda event: self.redo()) # Keyboard shortcut for redo

        # Suggestion Box
        self.suggestion_box = tk.Listbox(self, height=5)
        self.suggestion_box.place_forget()
        self.suggestion_box.bind("<Return>", self.insert_autocomplete)
        self.suggestion_box.bind("<Tab>", self.insert_autocomplete)
        self.suggestion_box.bind("<Up>", self.navigate_suggestions)
        self.suggestion_box.bind("<Down>", self.navigate_suggestions)

        # Bindings
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<Up>", self.navigate_suggestions)
        self.text_area.bind("<Down>", self.navigate_suggestions)
        self.text_area.bind("<space>", self.hide_suggestion_box)
        self.text_area.bind("<FocusOut>", self.hide_suggestion_box)
        self.text_area.bind("<Tab>", self.complete_autocomplete)
        self.text_area.bind("<MouseWheel>", self.on_mouse_wheel)
        self.text_area.bind("<Button-1>", self.on_click)
        self.text_area.bind("<Configure>", self.update_line_numbers)

        # Initialize line numbers
        self.update_line_numbers()

        # File Path
        self.file_path = None

        # Creating the buttons ribbon
        self.buttons_ribbon = ButtonsRibbon(self, self)
        self.buttons_ribbon.place(rely=0, anchor=tk.NW)
        self.buttons_ribbon.update_buttons()

        self.protocol("WM_DELETE_WINDOW", lambda: self.close())
    
    def update_line_numbers(self, event=None):
        line_count = int(self.text_area.index("end-1c").split('.')[0])
        self.line_numbers.config(state="normal")
        self.line_numbers.delete(1.0, "end")
        for i in range(1, line_count + 1):
            self.line_numbers.insert("end", f"{i}\n")
        self.line_numbers.config(state="disabled")

    def update_title(self):
        if self.file_path:
            filename = self.file_path.split("/")[-1]
            self.title(f"{filename} - Bestest Text Editor")
        else:
            self.title("Untitled - Bestest Text Editor")

    def position_suggestion_box(self):
        # Getting the current cursor position in the text area
        bbox = self.text_area.bbox("insert")
        if bbox:
            x, y, width, height = bbox
            # Adjust with text widget's absolute position
            abs_x = self.text_area.winfo_rootx() + x
            abs_y = self.text_area.winfo_rooty() + y + height
            self.suggestion_box.place(x=abs_x - self.winfo_rootx(), y=abs_y - self.winfo_rooty())
            self.suggestion_box.lift()

    def search_word(self):
        # Getting the word to search
        search_term = self.search_entry.get()
        if not search_term:
            messagebox.showinfo("Info", "Please enter a word to search.")
            return

        # Removing previous search highlights
        self.text_area.tag_remove("search_highlight", "1.0", "end")

        # Highlighting all occurrences of the search term
        start = "1.0"
        while True:
            start = self.text_area.search(search_term, start, stopindex="end", nocase=True)  # Case-insensitive search
            if not start:
                break
            end = f"{start}+{len(search_term)}c"
            self.text_area.tag_add("search_highlight", start, end)
            start = end
        self.text_area.tag_config("search_highlight", background="yellow")

    def undo(self):
        self.text_area.edit_undo()

    def redo(self):
        self.text_area.edit_redo()

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.text_area.selection_get())
    
    def paste(self):
        try:
            self.text_area.insert(tk.INSERT, self.clipboard_get())
        except tk.TclError:
            pass

    def save_file(self):
        if self.file_path:
            with open(self.file_path, "w") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
            messagebox.showinfo("Info", "File saved successfully!")
            self.update_title()
        else:
            self.save_as()

    def save_as(self):
        self.file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if self.file_path:
            with open(self.file_path, "w") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
            messagebox.showinfo("Info", "File saved successfully!")
            self.update_title()

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if self.file_path:
            with open(self.file_path, "r") as f:
                content = f.read()
            self.text_area.delete("1.0", "end-1c")
            self.text_area.insert("1.0", content)
            self.update_title()
    
    # Asking for confirmation to save changes when closing the app
    def close(self):
        if messagebox.askyesno("Exit", "Do you want to save before exiting?"):
            self.save_file()
        self.destroy()

    def on_key_release(self, event=None):
        # Skip autocomplete for arrow keys
        if event.keysym in ["Up", "Down"]:
            return
        self.text_area.edit_separator() # Ensures undo/redo is one letter at a time
        # Syntax highlighting function whenever a key is released
        syntax_highlight(self.text_area)
        self.autocomplete(event)
        self.update_line_numbers()

    def on_mouse_wheel(self, event):
        self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_click(self, event=None):
        self.line_numbers.yview_moveto(self.text_area.yview()[0])

    def hide_suggestion_box(self, event=None):
        self.suggestion_box.place_forget()  # Hiding the suggestion box
        self.suggestion_box.delete(0, tk.END)  # Clearing all suggestions

    def autocomplete(self, event):
        # Skip autocomplete if the space key was pressed
        if event.keysym == "space":
            return

        # Get the current word being typed
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.text_area.get(line_start, cursor_index)
        match = re.search(r"(\w+)$", current_line)  # Match the last word in the line
        last_word = match.group(1) if match else ""  # Extract the last word

        if not last_word:
            self.hide_suggestion_box()
            return

        # Show suggestions if the last word matches a keyword prefix
        suggestions = set(keyword.kwlist)
        matches = [word for word in suggestions if word.lower().startswith(last_word.lower())]

        if matches and last_word:  # Showing suggestions only if there are matches
            self.suggestion_box.delete(0, tk.END)  # Clearing all previous suggestions
            for match in matches:
                self.suggestion_box.insert(tk.END, match)

            # Selecting the first item by default
            self.suggestion_box.selection_clear(0, tk.END)
            self.suggestion_box.selection_set(0)
            self.suggestion_box.activate(0)

            # Positioning the suggestion box
            self.position_suggestion_box()
            self.suggestion_box.lift()
        else:
            # Hiding the suggestion box if no matches are found
            self.hide_suggestion_box()

    def insert_autocomplete(self, event):
        # Inserting the selected suggestion into the text area
        selected_word = self.suggestion_box.get(tk.ACTIVE)
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.text_area.get(line_start, cursor_index)
        last_word_start = current_line.rfind(current_line.split()[-1]) if current_line.split() else 0
        self.text_area.delete(f"{line_start}+{last_word_start}c", cursor_index)
        self.text_area.insert(tk.INSERT, selected_word)
        self.suggestion_box.pack_forget()

    def complete_autocomplete(self, event):
        if self.suggestion_box.winfo_ismapped():  # Checking if the suggestion box is visible
            selected_word = self.suggestion_box.get(tk.ACTIVE)
            if selected_word:
                cursor_index = self.text_area.index(tk.INSERT)
                line_start = f"{cursor_index.split('.')[0]}.0"
                current_line = self.text_area.get(line_start, cursor_index)
                last_word_start = current_line.rfind(current_line.split()[-1]) if current_line.split() else 0
                self.text_area.delete(f"{line_start}+{last_word_start}c", cursor_index)
                self.text_area.insert(tk.INSERT, selected_word)
                self.hide_suggestion_box()  # Hiding the suggestion box after inserting
            return "break"  # Preventing default Tab behavior
        return None  # Allowing default Tab behavior if no suggestion box is visible

    def navigate_suggestions(self, event):
        if self.suggestion_box.winfo_ismapped():  # Ensuring the suggestion box is visible
            size = self.suggestion_box.size()  # Getting the number of items in the Listbox
            if size == 0:
                return "break"  # No items to navigate

            try:
                index = self.suggestion_box.curselection()[0]  # Getting the current selection index
            except IndexError:
                index = -1  # No current selection

            # Updating the index based on the key pressed
            if event.keysym == "Down":
                index = (index + 1) % size  # Moving down, wrap around at the end
            elif event.keysym == "Up":
                index = (index - 1 + size) % size  # Moving up, wrap around at the top

            self.suggestion_box.selection_clear(0, tk.END)  # Clearing previous selection
            self.suggestion_box.selection_set(index)  # Setting the new selection
            self.suggestion_box.activate(index)  # Activating the new selection

            # Inserting the selected word into the text area, "inline preview"/"live suggestion"
            selected_word = self.suggestion_box.get(index) # Getting the selected word in the suggestion box
            cursor_index = self.text_area.index(tk.INSERT) # Getting the current cursor position
            line_start = f"{cursor_index.split('.')[0]}.0" # Determining the start of the line
            current_line = self.text_area.get(line_start, cursor_index) # Extract the text from the beginning of the line up to the cursor position

            if current_line.split():
                last_word = current_line.split()[-1] # Extract the word being autocompleted
                last_word_start = current_line.rfind(last_word) # Find the character position of the last word in the current line
                self.text_area.delete(f"{line_start}+{last_word_start}c", cursor_index) # Deleting the last word from the text area
                self.text_area.insert(tk.INSERT, selected_word) # Inserting the selected word from the suggestion box into the text area
                self.text_area.mark_set("insert", f"{line_start}+{last_word_start + len(selected_word)}c") # Move the insert cursor back to where it was

            return "break"  # Preventing default behavior of arrow keys
        return None  # Allowing default behavior if the suggestion box is not visible


# Running the Tkinter app
if __name__ == "__main__":
    app = NotesApp()
app.mainloop()
