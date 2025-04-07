import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from abc import ABC, abstractmethod
import sys

class ONote:
    def __init__(self, text: str, filename: str):
        self.text = text
        self.filename = filename

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        if not value:
            raise ValueError("Text cannot be empty")
        self.__text = value

    @property
    def filename(self):
        return self.__filename

    @filename.setter
    def filename(self, value):
        if not value:
            raise ValueError("Filename cannot be empty")
        self.__filename = value

    def save(self):
        try:
            with open(self.filename, 'w') as f:
                f.write(self.text)
        except Exception as e:
            raise e

    def read(self):
        try:
            with open(self.filename, 'r') as f:
                self.text = f.read()
        except Exception as e:
            raise e

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
    def __init__(self, parent, notes_app):
        super().__init__(parent)
        self.notes_app = notes_app
        
        self.new_btn = tk.Button(self, text="NEW", command=self.notes_app.new)
        self.open_btn = tk.Button(self, text="OPEN", command=self.notes_app.open)
        self.save_btn = tk.Button(self, text="SAVE", command=self.notes_app.save)
        self.save_as_btn = tk.Button(self, text="SAVE AS", command=self.notes_app.saveAs)
        self.close_btn = tk.Button(self, text="CLOSE", command=self.notes_app.close)
        
        self.buttons = [self.new_btn, self.open_btn, self.save_btn, self.save_as_btn, self.close_btn]
        for btn in self.buttons:
            btn.pack(side=tk.LEFT)
    
    def disable(self, nro):
        if 0 <= nro < len(self.buttons):
            self.buttons[nro].config(state="disabled")
        
    def update_buttons(self):
        self.new_btn.config(state="normal")
        self.open_btn.config(state="normal")
        self.close_btn.config(state="normal")
        
        if self.notes_app.textarea.get(1.0, tk.END).strip():
            if self.notes_app.onote:
                self.save_btn.config(state="normal")
                self.save_as_btn.config(state="normal")
            else:
                self.save_btn.config(state="disabled")
                self.save_as_btn.config(state="normal")
        else:
            self.save_btn.config(state="disabled")
            self.save_as_btn.config(state="disabled")

class Notes(tk.Tk):
    def new(self):
        self.textarea.delete(1.0, tk.END)
        self.onote = None

    def open(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self.textarea.delete(1.0, tk.END)
                self.textarea.insert(tk.END, content)
                self.onote = ONote(content, filename)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def save(self):
        if self.onote:
            self.onote.text = self.textarea.get(1.0, tk.END).strip()
            self.onote.save()
        else:
            self.saveAs()

    def saveAs(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.onote = ONote(self.textarea.get(1.0, tk.END).strip(), filename)
            self.onote.save()
    
    def close(self):
        if messagebox.askyesno("Exit", "Do you want to save before exiting?"):
            self.save()
        self.destroy()
    
    def __init__(self):
        super().__init__()
        self.title("Notes")
        self.geometry("600x400")
        self.onote = None

        self.buttons_ribbon = ButtonsRibbon(self, self)
        self.buttons_ribbon.pack(fill=tk.X)

        self.textarea = tk.Text(self)
        self.textarea.pack(expand=True, fill=tk.BOTH)

        self.protocol("WM_DELETE_WINDOW", lambda: self.close())

        self.textarea.bind("<KeyRelease>", lambda event: self.buttons_ribbon.update_buttons())

        self.buttons_ribbon.update_buttons()

        self.bind_all("<Control-s>", lambda event: self.save()) # Keyboard shortcut for save and save as
        self.bind_all("<Control-Shift-s>", lambda event: self.saveAs())

def main():
    s = ''  
    while True: 
        t = input(': ')
        if t.upper() != 'END':
            if t:
                s += t + '\n'
        elif s:
            try:                
                filename = input('Save to a file: ')
                cn = ONote(s, filename) 
                cn.save()  

                print()

                cn.read()  
                print('Text read back from ', cn.filename, ' is:')
                print(cn.text)
            except Exception as e:
                print(e) 
            break         
        else:
            break

if __name__=='__main__':
        if len(sys.argv) > 1 and sys.argv[1] == "-c":
            main()
        else:
            app = Notes()
            app.mainloop()
