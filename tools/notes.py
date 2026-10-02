import json   
import os

class NotesStore :
    def __init__(self , file_path = "data/notes.json") :
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path) , exist_ok = True)
        if not os.path.exists(self.file_path) :
            self._save([])

    def load_notes(self) -> list[str] :
        with open(self.file_path , "r" , encoding = "utf-8") as f :
            return json.load(f)

    def _save(self , notes: list[str]) -> None :
        with open(self.file_path , "w" , encoding = "utf-8") as f :
            json.dump(notes , f , ensure_ascii = False , indent = 2)

    def add_note(self , note: str) -> None :
        notes = self.load_notes()
        notes.append(note)
        self._save(notes)

    def remove_note(self , index: int) -> None :
        notes = self.load_notes()
        if 0 <= index < len(notes) :
            notes.pop(index)
            self._save(notes)



def save_note(note: str) -> None :
    store = NotesStore()
    store.add_note(note)

def get_notes() -> list[str] :
    store = NotesStore()
    return store.load_notes()
