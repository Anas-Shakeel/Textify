from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from PIL import ImageTk, Image
import os
import re
import time
import datetime
import pyperclip


# * Custom Functions
# ? Helper functions
def _reset_title():
    """Reset the program's title to default"""
    global program_title
    program_title = "Untitled"
    root.title(f"{program_title} - {PROGRAM_NAME}")


def _set_title_to(title):
    """Sets program's title to `title`"""
    global program_title
    program_title = title.replace("*", "")

    root.title(f"{title} - {PROGRAM_NAME}")


def _get_filename(filepath):
    """Returns the basename of `filepath`"""
    return os.path.basename(os.path.normpath(filepath))


def _modified(event=None):
    """
    ### Modified
    Sets the modified state to `True` if the content of text windget is modified, 
    `False` otherwise.
    """
    if modified:
        # ! IF modified == true? Return
        return

    if event.char and event.keysym not in unmod_keys:
        if text_area.edit_modified():
            _set_title_to(f"*{program_title}")
            _set_modified(True)


def _set_modified(b: bool):
    """
    Set the modified property to True or False
    """

    global modified
    modified = b


def _ask_to_save(name: str):
    """
    ### Ask to save
    Asks the user to save the file before proceeding
    """
    answer = messagebox.askyesnocancel(
        PROGRAM_NAME, f"Do you want to save changes to\n{name}?")

    return answer


def _on_key_release(event=None):
    """
    ### On Key Release
    Code to execute everytime a button or key is released (after being pressed!)
    """
    # execute only if status bar is visible!!
    if toggle_status_bar.get():
        _set_line_and_column()
        _set_chars_and_words()


def _get_cursor_position():
    """
    ### Cursor Position
    Returns the cursor's current position `(line, column)`
    """

    return text_area.index(INSERT).split(".")


def _set_line_and_column():
    """
    ### Set Line and Column
    updates the line and column info in the status bar
    """
    line_and_column = _get_cursor_position()
    cursor_info_label.config(
        text=f"Line: {line_and_column[0]} | Column: {line_and_column[1]}")


def _get_chars_and_words():
    """
    ### Get characters and words
    returns the number of characters and words in `text_area`
    """
    # get number of words
    words = len(text_area.get(1.0, "end - 1 chars").split())

    # get the number of characters
    chars = text_area.count(1.0, "end -1 chars", 'chars')

    # return the number of chars and words
    return 0 if chars == None else chars[0], words


def _set_chars_and_words():
    """
    ### Set Characters and words
    updates the characters and words in status bar
    """
    # get the characters and words from 'textarea'
    characters, words = _get_chars_and_words()
    # display them in statusbar
    chars_words_label.configure(
        text=f"Characters: {characters} | Words: {words}")


def _get_selection():
    """
    ### Get Selection
    returns the selected text and their first & last index

    ```
    >> # Format
    Tuple(tuple(indices), str(text))
    ```
    """

    # getting the text selection
    try:
        text = text_area.selection_get()
    except TclError:
        text = ""

    # getting the indices of selected text
    indices = text_area.tag_ranges(SEL)

    # returning both of them
    return indices, text


def _something_is_selected():
    """Returns `True`, if something is selected `False` otherwise"""
    try:
        return True if text_area.selection_get() else False
    except TclError:
        return False


def _menu_postcommand(event=None):
    """
    ### Menu PostCommand
    Code to execute whenever user presses on menus
    """
    # * decide & disable all commands

    selection_state = NORMAL
    clipboard_state = NORMAL
    undo_redo_state = NORMAL

    # selection state check
    if _something_is_selected():
        selection_state = NORMAL
    else:
        selection_state = DISABLED

    # clipboard state check
    try:
        root.clipboard_get()
    except TclError:
        clipboard_state = DISABLED

    # * enable/disable
    # Cut command
    menu_edit.entryconfig(3, state=selection_state)
    # copy command
    menu_edit.entryconfig(4, state=selection_state)
    # paste command
    menu_edit.entryconfig(5, state=clipboard_state)
    # delete command
    menu_edit.entryconfig(7, state=selection_state)


def _context_menu_postcommand(event=None):
    """
    ### Context Menu Postcommand
    Code to execute when user opens context menu
    """
    selection_state = NORMAL
    clipboard_state = NORMAL
    undo_redo_state = NORMAL

    # selection state check
    if _something_is_selected():
        selection_state = NORMAL
    else:
        selection_state = DISABLED

    # clipboard state check
    try:
        root.clipboard_get()
    except TclError:
        clipboard_state = DISABLED

    # * enable/disable
    # Cut command
    context_menu.entryconfig(3, state=selection_state)
    # copy command
    context_menu.entryconfig(4, state=selection_state)
    # paste command
    context_menu.entryconfig(5, state=clipboard_state)
    # delete command
    context_menu.entryconfig(6, state=selection_state)


def _search_all_matching_strings(string, textwidget):
    """
    ### Search words
    Search all matching `string` in `textwidget` and return the indices of 
    starting and ending index of each string in a generator of `tuples(index1, index2)`
    """
    # * search every string matching with `string`
    # get the required variables
    string_length = len(string)
    matches_found = 0

    # find the 'search_string' in 'text_widget'
    if string:
        start_pos = '1.0'
        while True:
            # 'search' returns the index of the first character found
            start_pos = textwidget.search(string, start_pos, END, nocase=False)

            if not start_pos:
                break

            end_pos = f'{start_pos} + {string_length} chars'

            # yield the found indices
            yield start_pos, end_pos

            matches_found += 1
            # set the start_pos for next iter. to current end_pos
            start_pos = end_pos


def _get_tag_words(tagname, textwidget, startpos, endpos):
    """
    ### Get tag words
    returns a generator of all tuples of indices of found characters with `tagname` tag.
    """
    start_pos = startpos
    while True:
        tag_indices = textwidget.tag_nextrange(tagname, start_pos, endpos)

        # if there is nothing in 'sel_indices', stop!!!
        if not tag_indices:
            break

        start_pos = tag_indices[-1]
        yield tag_indices


def _show_text_window(parent, data, title):
    """
    ### Show text window
    Displays a textwindow with `data` written to it!

    #### Used in About Window
    """
    text_win = Toplevel(parent)
    text_win.title(title)
    text_win.geometry("600x300+200+100")
    # text_win.transient(parent)
    text_win.focus()
    text_win.configure(padx=5, pady=5)
    text_mainframe = ttk.Frame(text_win)
    text_mainframe.grid(row=0, column=0, sticky=NSEW)

    # adding text widget
    text_widget = ScrolledText(text_win)
    text_widget.configure(borderwidth=1, relief="solid")
    text_widget.grid(row=0, column=0, sticky=NSEW)
    text_widget.insert("1.0", data)
    text_widget.configure(font=("Segoe UI", 17), wrap='word',
                          state="disabled", relief="flat")

    # responsiveness
    text_win.columnconfigure(0, weight=1)
    text_win.rowconfigure(0, weight=1)


# ? Context menu Functions
def _show_context_menu(event):
    """
    ### Show Context Menu
    Displays context menu in the text area
    """
    context_menu.tk_popup(event.x_root, event.y_root)


# ? Menu Functions
def _new(event=None):
    """
    ### New file
    Open a new file in the editor
    """
    global current_path

    if modified:
        # file is modified, ask to save first
        answer = _ask_to_save(program_title)

        if answer == None:
            # ? user cancelled! (Do nothing)
            return

        elif answer:
            # * Save
            # user agreed! (Save)
            if not current_path:
                # get the filepath
                current_path = filedialog.asksaveasfilename(
                    defaultextension=".txt", confirmoverwrite=True,
                    filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])

            # get the content
            content = text_area.get("1.0", "end - 1 chars")

            # save the content in current_path
            with open(current_path, "w") as newfile:
                newfile.write(content)

    # * finalizing stuff
    # clear the text_widget
    text_area.delete("1.0", END)

    # set modified to false
    _set_modified(False)

    # reset current_path
    current_path = ""

    # reset the title
    _reset_title()

    # reset Undo actions
    text_area.edit_reset()

    # update the status bar
    text_area.event_generate("<<update-statusbar>>")

    # return "break"


def _open(event=None):
    """
    ### Open a file

    # Bugs:
    after opening a file, if you edit the file, titles resets back to Untitled!
    """
    global current_path
    global modified

    if modified:
        answer = _ask_to_save(program_title)

        if answer == None:
            # ? Cancel (Do nothing)
            return

        elif answer:
            # * Save
            _save()

        else:
            # ! Don't save
            pass

    # open a dialog for file to open
    current_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[
                                              ("Text Documents", "*.txt"), ("All Files", "*.*")])

    if current_path:
        # delete the previous content
        text_area.delete("1.0", END)

        with open(current_path, encoding="utf-8") as file:
            text_area.insert("1.0", file.read())

        # set the title to 'current_path's basename
        _set_title_to(_get_filename(current_path))

        # reset Undo actions
        text_area.edit_reset()

        # update the status bar
        text_area.event_generate("<<update-statusbar>>")

    return "break"


def _save(event=None):
    """
    ### Save file
    Saves the content of 'text_area'  in a text file.

    # Bugs:
    after saving a file and creating a new, if you edit and save the file it will be saved
    to the older one you saved
    """
    global current_path

    # if current_path not set?
    if not current_path:
        # open a filesave dialog
        current_path = filedialog.asksaveasfilename(
            defaultextension=".txt", confirmoverwrite=True,
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])

    if current_path:
        # content to save
        content = text_area.get("1.0", "end - 1 chars")

        # save in current path
        with open(current_path, "w", encoding="utf-8") as file:
            file.write(content)

        # set modified to false
        _set_modified(False)

        # set title to filename
        _set_title_to(os.path.basename(os.path.normpath(current_path)))

    return "break"


def _save_as(event=None):
    """
    ### Save as
    Save as the current file
    """

    global current_path
    # content to save
    content = text_area.get("1.0", END)

    # open a filesave dialog
    current_path = filedialog.asksaveasfilename(
        defaultextension=".txt", confirmoverwrite=True,
        filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])

    if current_path:
        # save in current path
        with open(current_path, "w", encoding="utf-8") as file:
            file.write(content)

        # set title to filename
        _set_title_to(os.path.basename(os.path.normpath(current_path)))

    return "break"


def _file_properties(event=None):
    """
    ### File Properties
    Displays a dialog contating current file's properties
    """
    file_props_win = Toplevel(root)
    file_props_win.title(f"{program_title} Properties")
    file_props_win.geometry("350x500+200+120")
    file_props_win.resizable(False, False)
    file_props_win.transient(root)
    file_props_win.configure(padx=20, pady=20)

    # focus-in on it!
    file_props_win.focus()

    # Adding elements
    file_props_mainframe = ttk.Frame(
        file_props_win, borderwidth=12, relief="solid")
    file_props_mainframe.grid(row=0, column=0, sticky=(N, E, W, S))

    # Program Title
    ttk.Label(file_props_mainframe, text=PROGRAM_NAME, font=(
        "Roboto light", 20), justify="center").grid()

    # responsiveness
    file_props_win.columnconfigure(0, weight=1)
    file_props_win.rowconfigure(0, weight=1)

    return "break"


def _exit(event=None):
    """
    ### Quit the Application
    Code to execute when users try to close the application
    """
    # check if file has been modified?
    if modified:
        # popup a (file save) dialog
        answer = _ask_to_save(program_title)

        if answer:
            # save
            _save()

        if answer == None:
            # don't exit!
            return "break"

    # close the application
    root.quit()


def _undo(event=None):
    """
    ### Undo 
    Undo your actions
    """
    text_area.event_generate("<<Undo>>")
    text_area.event_generate("<<update-statusbar>>")
    return "break"


def _redo(event=None):
    """
    ### Redo
    Redo last actions
    """
    text_area.event_generate("<<Redo>>")
    text_area.event_generate("<<update-statusbar>>")
    return "break"


def _cut(event=None):
    """Cut the selection to clipboard"""
    # pyperclip.copy(text_area.selection_get())
    text_area.event_generate("<<Cut>>")
    text_area.event_generate("<<update-statusbar>>")
    return "break"


def _copy(event=None):
    """copy the selection to clipboard"""
    text_area.event_generate("<<Copy>>")
    text_area.event_generate("<<update-statusbar>>")
    return "break"


def _paste(event=None):
    """Paste the last copied item from clipboard into text widget"""
    text_area.event_generate("<<Paste>>")
    text_area.see("insert")
    text_area.event_generate("<<update-statusbar>>")
    return "break"


def _delete_selection(event=None):
    """
    ### Delete Selection
    Deletes the selected text, Can also be used with find dialog.

    #### Usage with find dialog:
    1. Search a string in find dialog and close the dialog.
    2. Press `Del` button or press `Edit > Delete Selection` button.
    3. This will delete all selected words/characters

    """
    # go through each 'indices-pair' and delete them
    for indices in _get_tag_words("sel", text_area, "1.0", END):
        text_area.delete(indices[0], indices[1])

    text_area.see("insert")

    # update the statusbar
    text_area.event_generate("<<update-statusbar>>")

    return "break"


def _delete_current_line(event=None):
    """
    ### Delete Current Line
    Deletes the currently active line
    """
    # should be disabled if:
    # the active is empty and the only line in text widget

    # delete it
    text_area.delete("insert linestart", "insert lineend + 1 chars")

    text_area.see("insert")

    # Update the statusbar
    text_area.event_generate("<<update-statusbar>>")

    return "break"
    ...


def _delete_all(event=None):
    """
    ### Delete All
    Clears the Text_area
    """
    text_area.delete(1.0, END)
    text_area.event_generate("<<update-statusbar>>")
    return "break"


def _find_replace_dialog(event=None):
    """
    ### Find & Replace Dialog
    Displays a `Find and replace` dialog.
    """
    find_win = Toplevel(root)
    find_win.geometry("370x120+100+150")
    find_win.title("Find & Replace...")
    find_win.focus()
    find_win.resizable(False, False)
    find_win.transient(root)
    find_win.config(padx=4, pady=4)

    # remove previously added SEL tag (removes prev. selections)
    text_area.tag_remove("sel", '1.0', END)

    # Closes the find dialog
    def _cancel_find():
        # Remove any tags
        ...
        # destroy the find dialog
        find_win.destroy()

    # finds the text
    def _find_text():
        """
        ### Find Text
        Finds the text from within `text_area`
        """
        # remove previously added SEL tag (removes prev. selections)
        text_area.tag_remove("sel", '1.0', END)

        # get the required variables
        match_case = not match_case_var.get()
        whole_word = whole_word_var.get()
        search_string = find_entry.get()
        matches_found = 0

        # find the 'search_string' in 'text_widget'
        if search_string:
            start_pos = '1.0'
            while True:
                # 'search' returns the index of the first character found
                start_pos = text_area.search(
                    search_string, start_pos, END, nocase=match_case,
                    exact=whole_word)

                if not start_pos:
                    break

                end_pos = f'{start_pos} + {len(search_string)} chars'

                # add 'sel' tag to found indices
                text_area.tag_add("sel", start_pos, end_pos)
                matches_found += 1
                # set the start_pos for next iter. to current end_pos
                start_pos = end_pos

            # focus on text widget
            text_area.focus_set()

    # replaces the text
    def _replace_text():
        """
        ### Replace text
        Replaces the tagged text with the given `word` or `string`.
        """
        # get the 'replace_with' string
        replace_string = replace_var.get()
        # print(replace_string)

        # go through each word in sel tag and replace it!
        for t in _get_tag_words("sel", text_area, '1.0', END):
            if t:
                text_area.replace(t[0], t[1], replace_string)

    find_win.protocol("WM_DELETE_WINDOW", _cancel_find)

    find_mainframe = ttk.Frame(find_win)
    # find_mainframe.configure(borderwidth=1, relief="solid")
    find_mainframe.grid(row=0, column=0, sticky=NSEW)

    # * 'fields' frame
    fields_frame = ttk.Frame(find_mainframe)
    fields_frame.grid(row=0, column=0, sticky=NSEW)
    # fields_frame.configure(borderwidth=2, relief="solid")

    # 'Find' row
    ttk.Label(fields_frame, text="Find what: ").grid(
        row=0, column=0, sticky=W)
    find_var = StringVar()
    find_entry = ttk.Entry(fields_frame, textvariable=find_var)
    find_entry.focus()
    find_entry.grid(row=0, column=1, sticky=(W, E))

    #  'Replace with' row
    ttk.Label(fields_frame, text="Replace with: ").grid(
        row=2, column=0, sticky=W)
    replace_var = StringVar()
    ttk.Entry(fields_frame, textvariable=replace_var).grid(
        row=2, column=1, sticky=(W, E))

    # ? 'Options' Row
    options_frame = ttk.Frame(fields_frame)
    # options_frame.config(borderwidth=2, relief="solid")
    options_frame.grid(row=3, column=0, columnspan=2, sticky=(S, W))

    # Match_case_checkbutton
    match_case_var = BooleanVar(value=True)
    match_case_check = ttk.Checkbutton(options_frame, text="Match Case",
                                       variable=match_case_var,
                                       onvalue=True, offvalue=False)
    match_case_check.grid(row=0, column=0, sticky=W)
    # match_case_check.invoke()

    # Whole_word_checkbutton
    whole_word_var = BooleanVar(value=False)
    whole_word_check = ttk.Checkbutton(options_frame, text="Whole Word",
                                       variable=whole_word_var,
                                       onvalue=True, offvalue=False)
    # whole_word_check.grid(row=0, column=1, sticky=W)
    # whole_word_check.invoke()

    # * 'Buttons' frame
    buttons_frame = ttk.Frame(find_mainframe)
    buttons_frame.grid(row=0, column=1, sticky=(S, N, E))
    # buttons_frame.configure(borderwidth=2, relief="solid")

    # find button
    ttk.Button(buttons_frame, text="Find All", command=_find_text).grid(
        row=0, column=0, sticky=E)

    # replace button
    ttk.Button(buttons_frame, text="Replace All", command=_replace_text).grid(
        row=1, column=0, sticky=E)

    # Cancel button
    ttk.Button(buttons_frame, text="Cancel", command=_cancel_find).grid(
        row=2, column=0, sticky=E)

    # * Spacing and padding
    for child in buttons_frame.winfo_children():
        child.grid_configure(pady=2)

    for child in fields_frame.winfo_children():
        child.grid_configure(pady=3)

    # * Responsiveness
    find_win.columnconfigure(0, weight=1)
    find_win.rowconfigure(0, weight=1)

    find_mainframe.columnconfigure(0, weight=15)
    find_mainframe.columnconfigure(1, weight=1)

    fields_frame.columnconfigure(1, weight=1)
    buttons_frame.columnconfigure(0, weight=1)

    return "break"


def _time_date(event=None):
    """
    ### Time/Date
    Insert 'Time & Date' at the cursor

    """
    t = time.localtime(time.time())
    dt = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday,
                           t.tm_hour, t.tm_min, t.tm_sec)
    time_date_var = f"{dt.strftime('%I:%M %p - %d %B %Y')}"
    text_area.insert("insert", time_date_var)

    text_area.see(INSERT)

    return "break"


def _select_all(event=None):
    """
    ### Select All
    Selects all text from the text_area widget
    """

    text_area.event_generate("<<SelectAll>>")
    return "break"


def _select_all_occurrences(event=None):
    """
    ### Select All Occurrences
    selects all occurrences of the select string.
    """
    # get the selection
    selected_text = _get_selection()[-1]

    # search all the matching strings and assign 'sel' to them
    for indices in _search_all_matching_strings(selected_text, text_area):
        text_area.tag_add('sel', indices[0], indices[1])

    return "break"


def _select_current_line(event=None):
    """
    ### Select Current Line
    Selects the current line (line with the insertion cursor)
    """
    # clear the previous selection
    text_area.tag_remove('sel', 1.0, END)

    # Select current line
    text_area.tag_add('sel', 'insert linestart', 'insert lineend + 1 chars')

    return "break"


def _word_wrap(event=None):
    """Enables or disables the wrap of 'text_view'"""
    if text_area['wrap'] == WORD or text_area['wrap'] == CHAR:
        # disable wrap
        text_area['wrap'] = NONE
        # show horizontal scrollbar
        scrollbar_horizon.grid(row=1, column=0, sticky=(S, E, W))

    else:
        # enable wrap
        text_area['wrap'] = WORD
        # hide horizontal scrollbar
        scrollbar_horizon.grid_forget()

    return "break"


def _highlight_active_line(interval=100):
    """
    ### Highlight active line
    Highlight currently active line
    """
    text_area.tag_remove("active_line", 1.0, END)
    text_area.tag_add("active_line", "insert linestart",
                      "insert lineend + 1 chars")
    text_area.after(interval, _toggle_highlight)


def _undo_highlight():
    text_area.tag_remove("active_line", 1.0, END)


def _toggle_highlight(event=None):
    """This function toggles highlight option"""
    if toggle_highlight_active_line.get():
        # toggle on
        _highlight_active_line()
    else:
        # toggle off
        _undo_highlight()


def _show_status_bar(event=None):
    """
    ### Show Status Bar
    """
    if toggle_status_bar.get():
        status_bar.grid(row=1, column=0, sticky=(W, E, S, N))

    else:
        status_bar.grid_forget()


def _fullscreen(event=None):
    """
    ### Fullscreen
    Enable or Disable fullscreen
    """
    global is_fullscreen

    if is_fullscreen:
        is_fullscreen = False
        # disable fullscreen
        root.attributes("-fullscreen", 0)
        menu_view.entryconfigure(3, indicatoron=False)

    else:
        is_fullscreen = True
        # enable fullscreen
        root.attributes("-fullscreen", 1)
        menu_view.entryconfigure(3, indicatoron=True)


def _font():
    ...


def _prefs(event=None):
    """
    ### Preferences
    Shows a preferences window
    """
    prefs_win = Toplevel(root)
    prefs_win.title("Preferences")
    prefs_win.geometry("400x600+200+100")
    prefs_win.resizable(False, False)
    prefs_win.transient(root)

    # ! prevent user to interact with root until this one is closed!
    prefs_win.grab_set()

    # focus on it!
    prefs_win.focus()

    ttk.Label(prefs_win, text="Preferences", font=(
        "Segoe UI", 20), justify="center").grid()

    return "break"


def _about(event=None):
    """Show About Window"""
    """
    Program Logo > done
    Program name: > done
    Description: > done
    Author: > done
    Source code link (github): > done
    
    License: 
    Privacy Policy
    """

    about_win = Toplevel(root)
    about_win.title(f"About {PROGRAM_NAME}")
    about_win.geometry("700x400+200+120")
    about_win.resizable(False, False)
    about_win.transient(root)
    about_win.configure(padx=20, pady=20)
    about_win.focus()

    # ! Prevent user to interact with root until this one is closed!
    # ! but when user minimizes the app while leaving it on, app won't then maximize again!
    # about_win.grab_set()

    def show_license_window(event=None):
        """
        ### Show License Window
        Triggers a toplevel window showing the content from `LICENSE` file
        """
        # call the 'show_text_window' function
        _show_text_window(parent=about_win, data=PROGRAM_LICENSE,
                          title=f"License - {PROGRAM_NAME}")

    # Adding elements
    about_mainframe = ttk.Frame(about_win)
    about_mainframe.grid(row=0, column=0, sticky=(N, E, W, S))

    # * Logo Frame
    logo_frame = ttk.Frame(about_mainframe)
    logo_frame.grid(row=0, column=0, sticky=(N, S, W, E))

    # * Program Logo image
    ttk.Label(logo_frame, image=PROGRAM_LOGO, padding="0 6").grid()

    # * Description Frame
    desc_frame = ttk.Frame(about_mainframe)
    desc_frame.grid(row=0, column=1, sticky=(N, W, E, S))
    # desc_frame.configure(borderwidth=2, relief="solid")

    # Program Description
    ttk.Label(desc_frame, text=PROGRAM_NAME, font=(
        "Calibri", 28)).grid(row=0, column=0, sticky=W)
    ttk.Label(desc_frame, text=f"Version ({PROGRAM_VERSION})", font=(
        "Calibri light", 14)).grid(row=0, column=1, sticky=S)
    ttk.Label(desc_frame, text=f"Written by {PROGRAM_AUTHOR}", font=(
        "Calibri light", 16)).grid(row=1, column=0, sticky=W)
    ttk.Label(desc_frame, padding="0 20",
              text=f"{PROGRAM_NAME} is a free text editor written completely in python that features rich tools for different tasks regarding searching, sorting, selecting, stripping, reversing and all the other 'ings'.",
              font=("Calibri", 13), wraplength=550).grid(row=2, column=0, columnspan=2, sticky=W)
    ttk.Label(desc_frame, padding="0 10 0 0",
              text=f"Source code for the program can be downloaded from the link below.",
              font=("Calibri", 13), wraplength=550).grid(row=3, column=0, columnspan=2, sticky=W)
    ttk.Label(desc_frame, text=f"{PROGRAM_SOURCE_CODE}", font=("Calibri bold", 13),
              wraplength=550).grid(row=4, column=0, columnspan=2, sticky=W)
    ttk.Button(desc_frame, text="Copy Url...", command=lambda e=None: pyperclip.copy(
        PROGRAM_SOURCE_CODE)).grid(row=4, column=1, sticky=W, padx=15)

    ttk.Button(desc_frame, text="License", command=show_license_window).grid(
        row=5, column=0, sticky=W, pady=10)

    # responsiveness
    about_win.rowconfigure(0, weight=1)
    about_win.columnconfigure(0, weight=1)
    about_mainframe.rowconfigure(0, weight=1)
    about_mainframe.columnconfigure(1, weight=1)

    return "break"


# ? Program functions
...


# ? CODE FOR THE UI
# * important program variables
PROGRAM_NAME = "Textify"
PROGRAM_VERSION = "1.0.0"
PROGRAM_AUTHOR = "Anas Shakeel"
PROGRAM_SOURCE_CODE = "https://github/Anas-Shakeel/Textify"
PROGRAM_LICENSE = """MIT License

Copyright (c) 2023 Anas Shakeel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
program_title = "Untitled"
current_path = ""
modified = False
is_fullscreen = False  # Keeps track of fullscreen or not
unmod_keys = {'Escape', 'Caps_Lock', 'Shift_L', 'Control_L', 'Win_L', 'Alt_L', 'Win_R', 'App', 'Control_R', 'Right',
              'Down', 'Left', 'Up', 'Num_Lock', 'Prior', 'Next', 'Home', 'End', 'Insert', 'F1', 'F2', 'F3', 'F4', 'F6', 'F7', 'F8', 'F9', 'F10'}


# * main root window
root = Tk()
root.geometry("1100x750+20+20")
root.minsize(350, 250)
root.title(f"{program_title} - {PROGRAM_NAME}")
root.option_add("*tearOff", FALSE) # disable menu tearoffs
root.protocol("WM_DELETE_WINDOW", _exit)
root.state("zoomed")  # app will open maximized by default

# setting Logo
PROGRAM_LOGO = ImageTk.PhotoImage(Image.open("assets\logo.ico"))
root.iconphoto(True, PROGRAM_LOGO)

# * creating the menu
menubar = Menu(root)
root['menu'] = menubar


""" Adding Menus """
# File Menu
menu_file = Menu(menubar)
menu_file.config(postcommand=_menu_postcommand)
menubar.add_cascade(menu=menu_file, label="File")
menu_file.add_command(label="New", command=_new, accelerator="Ctrl+N")
menu_file.add_command(label="Open...", command=_open, accelerator="Ctrl+O")
menu_file.add_command(label="Save", command=_save, accelerator="Ctrl+S")
menu_file.add_command(label="Save As...", command=_save_as,
                      accelerator="Ctrl+Shift+S")
menu_file.add_separator()
menu_file.add_command(label="File Properties",
                      command=_file_properties, accelerator="Ctrl+Shift+F")
menu_file.add_separator()
menu_file.add_command(label="Exit", command=_exit, accelerator="Ctrl+Q")

# Edit Menu
menu_edit = Menu(menubar)
menubar.add_cascade(menu=menu_edit, label="Edit")
menu_edit.add_command(label="Undo", command=_undo, accelerator="Ctrl+Z")
menu_edit.add_command(label="Redo", command=_redo, accelerator="Ctrl+Y")
menu_edit.add_separator()
menu_edit.add_command(label="Cut", command=_cut, accelerator="Ctrl+X")
menu_edit.add_command(label="Copy", command=_copy, accelerator="Ctrl+C")
menu_edit.add_command(label="Paste", command=_paste, accelerator="Ctrl+V")
menu_edit.add_separator()
menu_edit.add_command(label="Delete Selection",
                      command=_delete_selection, accelerator="Del")
menu_edit.add_command(label="Delete Current Line",
                      command=_delete_current_line, accelerator="Ctrl+Shift+K")
menu_edit.add_command(label="Delete All",
                      command=_delete_all, accelerator="Ctrl+Shift+Del")
menu_edit.add_separator()
menu_edit.add_command(label="Find & Replace",
                      command=_find_replace_dialog, accelerator="Ctrl+F")
menu_edit.add_separator()
menu_edit.add_command(label="Time/Date", command=_time_date, accelerator="F5")


# Selection Menu
menu_selection = Menu(menubar)
menubar.add_cascade(menu=menu_selection, label="Selection")
menu_selection.add_command(label="Select All",
                           command=_select_all, accelerator="Ctrl+A")
menu_selection.add_command(label="Select All Occurrences",
                           command=_select_all_occurrences, accelerator="Ctrl+Shift+L")
menu_selection.add_command(label="Select Current Line",
                           command=_select_current_line, accelerator="Ctrl+L")


# View Menu
menu_view = Menu(menubar)
menubar.add_cascade(menu=menu_view, label="View")

toggle_word_wrap = BooleanVar(value=True)
menu_view.add_checkbutton(indicatoron=True, onvalue=True, offvalue=False,
                          label="Word Wrap", variable=toggle_word_wrap, command=_word_wrap)

toggle_highlight_active_line = BooleanVar(value=False)
menu_view.add_checkbutton(label="Highlight Active Line", command=_highlight_active_line,
                          variable=toggle_highlight_active_line, onvalue=True, offvalue=False)
toggle_status_bar = BooleanVar(value=True)
menu_view.add_checkbutton(label="Status Bar", command=_show_status_bar, indicatoron=True,
                          variable=toggle_status_bar)

toggle_fullscreen = BooleanVar(value=False)
menu_view.add_checkbutton(label="Full Screen", command=_fullscreen, accelerator="F11",
                          indicatoron=False, onvalue=True, offvalue=False,
                          variable=toggle_fullscreen)


# Tools Menu
menu_tools = Menu(menubar)
menubar.add_cascade(menu=menu_tools, label="Tools")

""" Cascading Menu Template :: Study Thoroughly
test_menu = Menu(menu_tools)
menu_tools.add_cascade(menu=test_menu, label="Coming Soon...")
test_menu.add_command(label="Came")
 """

menu_tools.add_separator()
menu_tools.add_command(label="Preferences",
                       accelerator="Ctrl+Shift+P", command=_prefs)

# Help Menu
menu_help = Menu(menubar)
menubar.add_cascade(menu=menu_help, label="Help")
menu_help.add_command(label="About", command=_about, accelerator="F1")


# * Mainframe
mainframe = ttk.Frame(root)
mainframe.grid(row=0, column=0, sticky=(N, W, E, S))


# * Text_area
text_area = Text(mainframe, wrap="word", undo=1)
text_area.grid(row=0, column=0, sticky=(W, E, S, N))
text_area.configure(background="#eeeeee", relief="flat", padx=8, pady=4)
# text's styling
text_area.configure(font=("Segoe UI", 20),)
# cursor's styling
text_area.configure(insertbackground="#505050", insertwidth=1)
text_area.focus()
text_area.tag_config("active_line", background="#dddddd")


# * context menu
context_menu = Menu(text_area, postcommand=_context_menu_postcommand)
context_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=_undo)
context_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=_redo)
context_menu.add_separator()
context_menu.add_command(label="Cut", accelerator="Ctrl+X", command=_cut)
context_menu.add_command(label="Copy", accelerator="Ctrl+C", command=_copy)
context_menu.add_command(label="Paste", accelerator="Ctrl+V", command=_paste)
context_menu.add_command(label="Delete Selection",
                         accelerator="Del", command=_delete_selection)
context_menu.add_command(
    label="Delete All", accelerator="Ctrl+Shift+Del", command=_delete_all)
context_menu.add_separator()
context_menu.add_command(
    label="Select All", accelerator="Ctrl+A", command=_select_all)


# * scroll bar  -> Vertical
scrollbar = ttk.Scrollbar(
    mainframe, orient="vertical", command=text_area.yview)
scrollbar.grid(row=0, column=1, sticky=(N, E, S))
text_area.config(yscrollcommand=scrollbar.set)

# * scroll bar  -> Horizontal
scrollbar_horizon = ttk.Scrollbar(
    mainframe, orient="horizontal", command=text_area.xview)
scrollbar_horizon.grid(row=1, column=0, sticky=(S, E, W))
text_area.config(xscrollcommand=scrollbar_horizon.set)


# * Status bar
status_bar = ttk.Frame(root)
status_bar.grid(row=1, column=0, sticky=(W, E, S, N))
status_bar.config(borderwidth=1, relief="solid")

# Inner Frame
s_b_inner_frame = ttk.Frame(status_bar)
s_b_inner_frame.grid(row=0, column=0, ipadx=5, sticky=E)

# Cursor Info Label
cursor_info_label = ttk.Label(s_b_inner_frame, text="Line: 1 | Column: 1")
cursor_info_label.grid(row=0, column=0)
cursor_info_label.config(anchor="w", font=("Segoe UI", 10))

ttk.Separator(s_b_inner_frame, orient="vertical").grid(
    row=0, column=1, padx=20)

# Characters / words info Label
chars_words_label = ttk.Label(s_b_inner_frame, text="Characters: 0 | Words: 0")
chars_words_label.grid(row=0, column=2)
chars_words_label.config(anchor="w", font=("Segoe UI", 10))


# * Spacing and Padding >> Responsiveness
# root.config(padx=5, pady=3)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)
status_bar.columnconfigure(0, weight=1)


# * tag styling
# Selection tag config
text_area.tag_configure("sel", background="#15a1ff", foreground="white")


# * KeyBindings
text_area.bind("<Key>", _modified)
text_area.bind("<<Modified>>", _modified)
root.event_add("<<update-statusbar>>", "<KeyRelease>", "<ButtonRelease>")
text_area.bind("<<update-statusbar>>", _on_key_release)

# context menu
text_area.bind("<App>", _show_context_menu)  # for keyboard
text_area.bind("<Button-3>", _show_context_menu)  # for mouse

# file menu
root.bind("<Control-q>",  _exit)
root.bind("<Control-Q>",  _exit)
text_area.bind("<Control-n>", _new)
text_area.bind("<Control-N>", _new)
text_area.bind("<Control-o>", _open)
text_area.bind("<Control-O>", _open)
text_area.bind("<Control-s>", _save)
text_area.bind("<Control-S>", _save)
text_area.bind("<Control-Shift-s>", _save_as)
text_area.bind("<Control-Shift-S>", _save_as)
text_area.bind("<Control-Shift-f>", _file_properties)
text_area.bind("<Control-Shift-F>", _file_properties)

# edit menu
text_area.bind("<Control-z>", _undo)
text_area.bind("<Control-Z>", _undo)
text_area.bind("<Control-Y>", _redo)
text_area.bind("<Control-y>", _redo)
text_area.bind("<Control-X>", _cut)
text_area.bind("<Control-x>", _cut)
text_area.bind("<Control-c>", _copy)
text_area.bind("<Control-C>", _copy)
text_area.bind("<Control-v>", _paste)
text_area.bind("<Control-V>", _paste)
text_area.bind("<Delete>", _delete_selection)
text_area.bind("<Control-Shift-k>", _delete_current_line)
text_area.bind("<Control-Shift-K>", _delete_current_line)
text_area.bind("<Control-Shift-Delete>", _delete_all)
text_area.bind("<Control-F>", _find_replace_dialog)
text_area.bind("<Control-f>", _find_replace_dialog)
text_area.bind("<KeyPress-F5>", _time_date)

# selection menu
text_area.bind("<Control-a>", _select_all)
text_area.bind("<Control-Shift-l>", _select_all_occurrences)
text_area.bind("<Control-Shift-L>", _select_all_occurrences)
text_area.bind("<Control-l>", _select_current_line)
text_area.bind("<Control-L>", _select_current_line)

# view menu
# text_area.bind("<Alt-z>", _word_wrap)
# text_area.bind("<Alt-Z>", _word_wrap)
# text_area.bind("<Alt-h>", _highlight_active_line)
# text_area.bind("<Alt-H>", _highlight_active_line)
text_area.bind("<KeyPress-F11>", _fullscreen)

# tools menu
text_area.bind("<Control-Shift-p>", _prefs)
text_area.bind("<Control-Shift-P>", _prefs)

# help menu
text_area.bind("<KeyPress-F1>", _about)


# ? DEBUG MODE :: REMOVE AFTERWARDS
def DEBUG():
    #  LOAD A DEMO FILE
    with open('download.txt', encoding="utf-8") as demofile:
        text_area.insert("1.0", demofile.read())

    # set the title to 'current_path's basename
    _set_title_to(_get_filename(current_path))

    # reset Undo actions
    text_area.edit_reset()

    # update the status bar
    text_area.event_generate("<<update-statusbar>>")


# DEBUG()

root.mainloop()
