import tkinter as tk
from tkinter import filedialog, messagebox, Text, ttk
from abc import ABC, abstractmethod
import keyword

# Defining syntax highlighting function
def syntax_highlight(text_widget: Text):
    text_widget.get("1.0", "end-1c")  # Get all text from Text widget

    # Removing previous tags for syntax highlighting
    text_widget.tag_remove("keyword", "1.0", "end")
    text_widget.tag_remove("string", "1.0", "end")
    text_widget.tag_remove("comment", "1.0", "end")

    # Highlighting keywords in blue
    for word in keyword.kwlist:  # Python keywords from keyword
        start = "1.0"
        while True:
            start = text_widget.search(rf"\b{word}\b", start, stopindex="end", regexp=True)
            if not start:
                break
            end = f"{start}+{len(word)}c"
            text_widget.tag_add("keyword", start, end)
            start = end
    text_widget.tag_config("keyword", foreground="blue", font=("Arial", 10, "bold"))

    # Highlighting strings in green
    start = "1.0"
    while True:
        start = text_widget.search(r'".*?"', start, stopindex="end", regexp=True)
        if not start:
            break
        end = f"{start}+{len(text_widget.get(start, start + '+1c'))}c"
        text_widget.tag_add("string", start, end)
        start = end
    text_widget.tag_config("string", foreground="green", font=("Arial", 10, "italic"))

    # Highlighting comments in gray
    start = "1.0"
    while True:
        start = text_widget.search(r"#.*", start, stopindex="end", regexp=True)
        if not start:
            break
        end = f"{start}+{len(text_widget.get(start, start + '+1c'))}c"
        text_widget.tag_add("comment", start, end)
        start = end
    text_widget.tag_config("comment", foreground="gray", font=("Arial", 10, "italic"))

# Autocomplete function for Python keywords
def autocomplete(event, text_widget: Text):
    typed_text = text_widget.get("insert-1c", "insert")  # Get last typed character

    # Finding the current word typed
    words = typed_text.split()
    if words:
        last_word = words[-1]

        # Finding matching keywords from Python's keyword list
        matches = [kw for kw in keyword.kwlist if kw.startswith(last_word)]

        if matches:
            # The first match and replacing the current word with the complete keyword
            match = matches[0]
            start_pos = "insert-1c linestart"
            end_pos = "insert"
            text_widget.delete(start_pos, end_pos)  # Removing the incomplete word
            text_widget.insert("insert", match)  # Inserting the matching keyword

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
        self.close_btn = tk.Button(self, text="CLOSE", command=self.NotesApp.close)
        
        self.buttons = [self.undo_btn, self.redo_btn, self.close_btn]
        for btn in self.buttons:
            btn.pack(side=tk.LEFT)
    
    def disable(self, nro):
        if 0 <= nro < len(self.buttons):
            self.buttons[nro].config(state="disabled")
        
    def update_buttons(self):
        self.undo_btn.config(state="normal")
        self.redo_btn.config(state="normal")
        self.close_btn.config(state="normal")

# Sample Tkinter Application
class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bestest Text Editor")
        self.geometry("600x400")
        # Creating a frame for buttons and search bar
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        menu_bar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Attaching the menu bar
        self.config(menu=menu_bar)

        # Search Bar
        self.search_button = tk.Button(self.top_frame, text="Search", command=self.search_word, bg="lightblue")
        self.search_button.pack(side=tk.RIGHT, padx=5)

        self.search_entry = tk.Entry(self.top_frame, width=20)  # Set the width to 20
        self.search_entry.pack(side=tk.RIGHT, fill=tk.X, expand=False)  # Remove expand=True

        # Creating a Text widget
        self.text_area = tk.Text(self, wrap="word", undo=True, bg="#ffffff", highlightthickness=0, relief="flat")
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # Binding key release event to apply syntax highlighting
        self.text_area.bind("<KeyRelease>", self.on_key_release)

        # Binding the autocomplete function on TAB key press
        self.text_area.bind("<Tab>", self.on_tab_press)

        # File path
        self.file_path = None

        # Autocomplete suggestions
        self.suggestion_box = tk.Listbox(self, height=5)
        self.suggestion_box.pack_forget()  # Initially hidden
        self.suggestion_box.bind("<<ListboxSelect>>", self.insert_autocomplete)

        # Ask for confirmation before closing the window
        self.protocol("WM_DELETE_WINDOW", lambda: self.close())

        # Creating the buttons ribbon
        self.buttons_ribbon = ButtonsRibbon(self, self)
        self.buttons_ribbon.pack(side=tk.TOP, fill=tk.X)
        self.buttons_ribbon.place(rely=0, anchor=tk.NW)
        self.buttons_ribbon.update_buttons()

    def position_suggestion_box(self):
        # Calculate the width of window
        window_width = self.winfo_width()

        # The width of the suggestion box
        suggestion_box_width = self.suggestion_box.winfo_reqwidth()

        x_position = self.winfo_rootx() # no padding from the right side
        y_position = self.winfo_rooty() + 30  # Fixed 30 pixels from the top

        # Placing the suggestion box at the calculated position
        self.suggestion_box.place(x=x_position, y=y_position)
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
            start = self.text_area.search(search_term, start, stopindex="end")
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

    def save_file(self):
        if self.file_path:
            with open(self.file_path, "w") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
            messagebox.showinfo("Info", "File saved successfully!")
        else:
            self.save_as()

    def save_as(self):
        self.file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if self.file_path:
            with open(self.file_path, "w") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
            messagebox.showinfo("Info", "File saved successfully!")

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if self.file_path:
            with open(self.file_path, "r") as f:
                content = f.read()
            self.text_area.delete("1.0", "end-1c")
            self.text_area.insert("1.0", content)
    
    # Close the application and ask for confirmation to save changes
    def close(self):
        if messagebox.askyesno("Exit", "Do you want to save before exiting?"):
            self.save_file()
        self.destroy()

    def on_key_release(self, event=None):
        # Syntax highlighting function whenever a key is released
        syntax_highlight(self.text_area)
        self.autocomplete(event)

    def on_tab_press(self, event=None):
        # Inserting tab spaces
        event.widget.insert(tk.INSERT, " " * 4)  # Insert 4 spaces for tab

        # Calling autocomplete function
        autocomplete(event, self.text_area)
        return "break"  # Preventing default tab insertion behavior

    def autocomplete(self, event):
        # Getting the current word being typed
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.text_area.get(line_start, cursor_index)
        last_word = current_line.split()[-1] if current_line.split() else ""

        # Gathering suggestions (Python keywords)
        suggestions = set(keyword.kwlist)
        text_content = self.text_area.get("1.0", "end-1c")
        suggestions.update(set(text_content.split()))
        matches = [word for word in suggestions if word.lower().startswith(last_word.lower())]

        # Display suggestions in the dropdown
        if matches:
            self.suggestion_box.delete(0, tk.END)
            for match in matches:
                self.suggestion_box.insert(tk.END, match)

            # Calling position_suggestion_box method to place the suggestion box
            self.position_suggestion_box()
        else:
            self.suggestion_box.pack_forget()

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

# Running the Tkinter app
if __name__ == "__main__":
    app = NotesApp()
app.mainloop()
