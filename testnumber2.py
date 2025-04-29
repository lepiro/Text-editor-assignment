import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from abc import ABC, abstractmethod
import re
import keyword

class DLLNode:
    def __init__(self, char):
        self.char = char
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = DLLNode("")
        self.tail = self.head

    def insert(self, index, char):
        node = DLLNode(char)
        curr = self.head
        for _ in range(index):
            if curr.next: curr = curr.next
        node.prev = curr
        node.next = curr.next
        if curr.next: curr.next.prev = node
        curr.next = node
        if node.next is None:
            self.tail = node

    def delete(self, index):
        curr = self.head
        for _ in range(index):
            if curr.next: curr = curr.next
        deleted = curr.next
        if deleted:
            curr.next = deleted.next
            if deleted.next: deleted.next.prev = curr
            return deleted.char
        return ""

    def get_text(self):
        chars = []
        curr = self.head.next
        while curr:
            chars.append(curr.char)
            curr = curr.next
        return "".join(chars)

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
        #self.copy_btn = tk.Button(self, text="COPY", command=self.NotesApp.copy)
        #self.paste_btn = tk.Button(self, text="PASTE", command=self.NotesApp.paste)
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
        #self.copy_btn.config(state="normal")
        #self.paste_btn.config(state="normal")
        self.close_btn.config(state="normal")

class UndoStack:
    def __init__(self):
        self.stack = []
        self.redo_stack = []

    def push(self, action, index, char):
        self.stack.append((action, index, char))
        self.redo_stack.clear()

    def pop(self):
        return self.stack.pop() if self.stack else None

    def push_redo(self, action):
        self.redo_stack.append(action)

    def redo(self):
        return self.redo_stack.pop() if self.redo_stack else None

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def autocomplete(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        return self._dfs(node, prefix)

    def _dfs(self, node, prefix):
        result = []
        if node.is_end:
            result.append(prefix)
        for ch, child in node.children.items():
            result.extend(self._dfs(child, prefix + ch))
        return result

class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bestest Text Editor")

        self.dll = DoublyLinkedList()
        self.undo_stack = UndoStack()
        self.trie = Trie()

        # Top Frame
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(fill='x', side='top')

        # Search Bar
        self.search_entry = tk.Entry(self.top_frame, width=20)
        self.search_entry.pack(side=tk.RIGHT, padx=5)
        self.search_button = tk.Button(self.top_frame, text="Search", command=self.search_word, bg="lightblue")
        self.search_button.pack(side=tk.RIGHT, padx=5)

        self.text_area = tk.Text(self, wrap='word')
        self.text_area.pack(expand=1, fill=tk.BOTH)
        self.text_area.bind("<Key>", self.on_key)
        self.text_area.bind("<space>", self.add_to_trie)
        self.text_area.bind("<Up>", self.navigate_suggestions)
        self.text_area.bind("<Down>", self.navigate_suggestions)
        self.text_area.bind("<Return>", self.select_suggestion)
        self.text_area.bind("<Tab>", self.select_suggestion)
        self.text_area.bind("<Control-s>", self.save_file, add=True)
        self.text_area.bind("<Control-o>", self.open_file, add=True)
        self.text_area.bind("<Control-z>", self.undo, add=True)
        self.text_area.bind("<Control-y>", self.redo, add=True)

        self.suggestion_box = tk.Listbox(self, height=5)
        self.suggestion_box.place_forget()  # Hide the suggestion box initially
        self.suggestion_box.bind("<Double-Button-1>", self.select_suggestion)
        self.suggestion_box.bind("<Tab>", self.insert_autocomplete)
        self.suggestion_box.bind("<Up>", self.navigate_suggestions)
        self.suggestion_box.bind("<Down>", self.navigate_suggestions)
        self.suggestion_box.bind("<space>", self.hide_suggestion_box)

        # Menu Bar
        self.menu_bar = tk.Menu(self)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        self.config(menu=self.menu_bar)

        for word in keyword.kwlist:
            self.trie.insert(word)

        # Creating the buttons ribbon
        self.buttons_ribbon = ButtonsRibbon(self, self)
        self.buttons_ribbon.place(rely=0, anchor=tk.NW)
        self.buttons_ribbon.update_buttons()

        self.protocol("WM_DELETE_WINDOW", lambda: self.close())

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

    def on_key(self, event):
        # Handle key press events
        if event.keysym == 'BackSpace':
            idx = self.get_cursor_index() - 1
            if idx >= 0:  # Ensure the index is valid
                deleted = self.dll.delete(idx)
                if deleted:
                    self.undo_stack.push('delete', idx, deleted)
                    self.refresh_text()
                    self.update_suggestions()
        elif event.char.isprintable():
            idx = self.get_cursor_index()
            self.dll.insert(idx, event.char)
            self.undo_stack.push('insert', idx, event.char)
            self.refresh_text()
            self.update_suggestions()
        self.highlight_syntax()

        # Prevent the default behavior of the Text widget
        return "break"

    def undo(self, event=None):
        # undo
        action = self.undo_stack.pop()
        if not action:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return

        act, idx, char = action
        if act == 'insert':
            self.dll.delete(idx)
            self.undo_stack.push_redo(('insert', idx, char))  # Push to redo stack
        elif act == 'delete':
            self.dll.insert(idx, char)
            self.undo_stack.push_redo(('delete', idx, char))  # Push to redo stack

        # Refresh the text area and syntax highlighting
        self.refresh_text()
        self.highlight_syntax()

    def redo(self, event=None):
        # redo
        action = self.undo_stack.redo()
        if not action:
            messagebox.showinfo("Redo", "Nothing to redo.")
            return

        act, idx, char = action
        if act == 'insert':
            self.dll.insert(idx, char)
            self.undo_stack.push('insert', idx, char)  # Push back to undo stack
        elif act == 'delete':
            self.dll.delete(idx)
            self.undo_stack.push('delete', idx, char)  # Push back to undo stack

        # Refresh the text area and syntax highlighting
        self.refresh_text()
        self.highlight_syntax()

    def update_title(self):
        if self.file_path:
            filename = self.file_path.split("/")[-1]
            self.title(f"{filename} - Bestest Text Editor")
        else:
            self.title("Untitled - Bestest Text Editor")

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
        result = messagebox.askyesnocancel("Exit", "Do you want to save before exiting?")
        if result is True:
            self.save_file()
            self.destroy()
        elif result is False:
            self.destroy()

    def add_to_trie(self, event):
        # Add the last word to the trie when space is pressed.
        words = self.dll.get_text().split()
        if words:
            last_word = words[-1].strip()
            if last_word:  # Ensure the last word is not empty
                self.trie.insert(last_word)

        # Reinsert the space into the text
        idx = self.get_cursor_index()
        self.dll.insert(idx, " ")
        self.refresh_text()

        # Prevent the default behavior of the Text widget
        return "break"
    
    def autocomplete(self, event):
        if event.keysym == "space":
            return

        # Get the current word being typed
        cursor_index = self.text_area.index(tk.INSERT)
        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.text_area.get(line_start, cursor_index)
        match = re.search(r"(\w+)$", current_line)
        last_word = match.group(1) if match else ""

        if not last_word:
            self.hide_suggestion_box()
            return

        # Use Trie to find matching words
        matches = self.trie.autocomplete(last_word)

        if matches:
            self.suggestion_box.delete(0, tk.END)
            for match in matches:
                self.suggestion_box.insert(tk.END, match)

            self.suggestion_box.selection_clear(0, tk.END)
            self.suggestion_box.selection_set(0)
            self.suggestion_box.activate(0)

            self.suggestion_box.lift()
        else:
            self.hide_suggestion_box()

    def insert_autocomplete(self, event):
        selected_word = self.suggestion_box.get(tk.ACTIVE)
        if not selected_word:
            return

        cursor_index = self.text_area.index(tk.INSERT)
        line_start = f"{cursor_index.split('.')[0]}.0"
        current_line = self.text_area.get(line_start, cursor_index)

        match = re.search(r"(\w+)$", current_line)
        if match:
            last_word_start = match.start(1)
            self.text_area.delete(f"{line_start}+{last_word_start}c", cursor_index)
        self.text_area.insert(tk.INSERT, selected_word)
        self.hide_suggestion_box()

    def complete_autocomplete(self, event):
        if self.suggestion_box.winfo_ismapped():
            self.insert_autocomplete(event)
            return "break"
        return None
    
    def hide_suggestion_box(self, event=None):
        self.suggestion_box.place_forget()  # Hiding the suggestion box
        self.suggestion_box.delete(0, tk.END)  # Clearing all suggestions

    def navigate_suggestions(self, event):
        if self.suggestion_box.winfo_ismapped():
            size = self.suggestion_box.size()
            if size == 0:
                return "break"

            try:
                index = self.suggestion_box.curselection()[0]
            except IndexError:
                index = -1

            if event.keysym == "Down":
                index = (index + 1) % size
            elif event.keysym == "Up":
                index = (index - 1 + size) % size

            self.suggestion_box.selection_clear(0, tk.END)
            self.suggestion_box.selection_set(index)
            self.suggestion_box.activate(index)

            return "break"
        return None

    def update_suggestions(self):
        # Update the autocomplete suggestion box
        idx = self.get_cursor_index()
        text = self.dll.get_text()[:idx]
        word = text.split()[-1] if text.split() else ""
        suggestions = self.trie.autocomplete(word)

        # Clear the suggestion box
        self.suggestion_box.delete(0, tk.END)

        if suggestions:
            # Populate the suggestion box with matching words
            for suggestion in suggestions[:5]:
                self.suggestion_box.insert(tk.END, suggestion)
            self.suggestion_box.selection_clear(0, tk.END)
            self.suggestion_box.selection_set(0)

            # Position the suggestion box near the cursor
            bbox = self.text_area.bbox(tk.INSERT)
            if bbox:
                x, y, width, height = bbox
                abs_x = self.text_area.winfo_rootx() + x
                abs_y = self.text_area.winfo_rooty() + y + height
                self.suggestion_box.place(x=abs_x - self.winfo_rootx(), y=abs_y - self.winfo_rooty())
                self.suggestion_box.lift()
        else:
            # Hide the suggestion box if no matches are found
            self.suggestion_box.place_forget()

    def select_suggestion(self, event=None):
        # Handle the Enter key for selecting suggestions/inserting a new line 
        if self.suggestion_box.winfo_ismapped():
            # If the suggestion box is visible, select the suggestion
            selection = self.suggestion_box.curselection()
            if not selection:
                return "break"
            word = self.suggestion_box.get(selection[0])
            idx = self.get_cursor_index()
            text = self.dll.get_text()[:idx]
            parts = text.split()
            if not parts:
                return "break"
            start_idx = idx - len(parts[-1])
            for _ in range(len(parts[-1])):
                self.dll.delete(start_idx)
            for i, c in enumerate(word):
                self.dll.insert(start_idx + i, c)
            self.refresh_text()
            self.suggestion_box.place_forget()
            self.highlight_syntax()
            return "break"
        else:
            # If the suggestion box is not visible, allow the default behavior (newline)
            return None

    def refresh_text(self):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", self.dll.get_text())

    def get_cursor_index(self):
        index = self.text_area.index(tk.INSERT)
        line, col = map(int, index.split("."))
        text = self.text_area.get("1.0", index)
        return sum(len(line) + 1 for line in text.splitlines()[:line - 1]) + col

    def highlight_syntax(self):
        # Highlight Python keywords and strings in the Text widget.
        # Remove previous tags
        self.text_area.tag_remove("keyword", "1.0", tk.END)
        self.text_area.tag_remove("string", "1.0", tk.END)

        # Highlight keywords
        text = self.dll.get_text()
        for word in keyword.kwlist:
            start = "1.0"
            while True:
                # Search for the keyword in the text
                pos = self.text_area.search(rf"\b{word}\b", start, stopindex=tk.END, regexp=True)
                if not pos:
                    break
                end = f"{pos}+{len(word)}c"
                self.text_area.tag_add("keyword", pos, end)
                start = end

        # Highlight strings
        start = "1.0"
        while True:
            # Search for strings enclosed in double quotes
            start = self.text_area.search(r'"', start, stopindex=tk.END, regexp=False)
            if not start:
                break
            end = self.text_area.search(r'"', f"{start}+1c", stopindex=tk.END, regexp=False)
            if not end:
                # If no closing quote is found, highlight until the end of the text
                end = tk.END
            else:
                end = f"{end}+1c"  # Include the closing quote
            self.text_area.tag_add("string", start, end)
            start = end

        # Configure the tags
        self.text_area.tag_config("keyword", foreground="blue", font=("Arial", 10, "bold"))
        self.text_area.tag_config("string", foreground="green", font=("Arial", 10, "italic"))

if __name__ == "__main__":
    app = NotesApp()
    app.mainloop()
