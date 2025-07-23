import glob
import json
import os
import re
import tkinter as tk
import tkinter.filedialog as tkf
import tomllib
import zipfile

# pip install packaging
from packaging.version import Version
from packaging.specifiers import SpecifierSet


class Main():

    def __init__(self, root):
        
        self.set_translation_key()
        
        self.mods_dir = ""

        self.EXCLUDE_DEPENDS = ["minecraft", "java", "fabricloader", "neoforge"]

        self.result_data = {}

        self.root = root
        self.root.title("MCAutoDepMods")
        
        self.selected_lang = tk.StringVar()

        self.menu_bar = tk.Menu(master=root)
        self.root.config(menu=self.menu_bar)
        
        self.error_toplevel = None

        self.file_menu = tk.Menu(master=self.menu_bar, tearoff=False)

        self.setting_menu = tk.Menu(master=self.menu_bar, tearoff=False)
        self.lang_menu = tk.Menu(master=self.setting_menu, tearoff=False)

        self.help_menu = tk.Menu(master=self.menu_bar, tearoff=False)
        
        self.output_frame = tk.Frame(master=self.root)

        self.output_text_scrollbar = tk.Scrollbar(master=self.output_frame)

        self.output_text_box = tk.Text(master=self.output_frame,state="disabled", yscrollcommand=self.output_text_scrollbar.set)

        self.output_text_scrollbar.config(command=self.output_text_box.yview)
        
        
        self.root.bind_all("<Control-o>", lambda e: self.open_mods_dir())
        self.root.bind_all("<Control-r>", lambda e: self.load_mods_dir())
        
        


        self.output_frame.pack(fill="both", expand=True)
        self.output_text_scrollbar.pack(side="right", fill="y")
        self.output_text_box.pack(side="left", fill="both", expand=True)
        
        self.build_menu()
    
    def build_menu(self):
        self.root.title(self.tr("MCAutoDepMods.window.main.title"))
        self.root.config(menu=None)
        
        self.menu_bar.delete(0, "end")
        
        self.lang_menu.delete(0, "end")
        self.file_menu.delete(0, "end")
        self.setting_menu.delete(0, "end")
        self.help_menu.delete(0, "end")
        
        self.file_menu.add_command(label=self.tr("MCAutoDepMods.window.main.menu.file.open_mods_dir"), accelerator="Ctrl+O", command=self.open_mods_dir)
        self.file_menu.add_command(label=self.tr("MCAutoDepMods.window.main.menu.file.reload"), accelerator="Ctrl+R", command=self.load_mods_dir)
        
        for code in self.translations["lang_desc"].keys():
            self.lang_menu.add_radiobutton(label=self.translations["lang_desc"][code], value=code, variable=self.selected_lang, command=self.update_language)
        
        self.setting_menu.add_cascade(label=self.tr("MCAutoDepMods.window.main.menu.config.language"), menu=self.lang_menu)
        self.menu_bar.add_cascade(label=self.tr("MCAutoDepMods.window.main.menu.file"), menu=self.file_menu)
        self.menu_bar.add_cascade(label=self.tr("MCAutoDepMods.window.main.menu.config"), menu=self.setting_menu)
        self.menu_bar.add_cascade(label=self.tr("MCAutoDepMods.window.main.menu.help"), menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def update_language(self):
        if not self.selected_lang.get() == self.current_lang:
            self.current_lang = self.selected_lang.get()
            self.root.after(1, self.build_menu)
    
    def set_translation_key(self):
        self.current_lang = "ja-JP"
        self.translations = {
            "lang_desc": {
                "ja-JP": "日本語",
                "en-US": "English"
            },
            "ja-JP": {
                "MCAutoDepMods.window.main.title": "MCAutoDepMods",
                "MCAutoDepMods.window.main.menu.file": "ファイル",
                "MCAutoDepMods.window.main.menu.file.open_mods_dir": "modsディレクトリを開く",
                "MCAutoDepMods.window.main.menu.file.reload": "再読み込み",
                "MCAutoDepMods.window.main.menu.config": "設定",
                "MCAutoDepMods.window.main.menu.config.language": "言語設定",
                "MCAutoDepMods.window.main.menu.help": "ヘルプ",
                "MCAutoDepMods.window.main.msg.title": "[検索先ディレクトリ] {mods_dir}\n[見つかったjarファイル] {file_count}個\n[見つからなかった依存関係] {missing_dep_count}個(内訳  fabric:{fabric_count}, neoforge:{neoforge_count})\n",
                "MCAutoDepMods.window.main.msg.loader.list.title": "\n{loader} x{count}",
                "MCAutoDepMods.window.main.msg.loader.list.item": "\n|- [{loader}] {dep}  [version] {version}\n|",
                "MCAutoDepMods.window.main.msg.loader.list.end": "__\n",
                "MCAutoDepMods.window.open_dir.title": "modsディレクトリを選択",
                "MCAutoDepMods.window.error.title": "MCAutoDepMods -ERROR",
                "MCAutoDepMods.window.error.msg.title": "このエラーをコピーし開発者に送信してください。",
                "MCAutoDepMods.window.error.msg.text.load_error": "{file}の読み込み中にエラーが発生しました",
                "MCAutoDepMods.window.error.msg.text.read_error": "{file}から情報取得中にエラーが発生しました"
            },
            "en-US": {
                "MCAutoDepMods.window.main.title": "MCAutoDepMods",
                "MCAutoDepMods.window.main.menu.file": "File",
                "MCAutoDepMods.window.main.menu.file.open_mods_dir": "Open mods directory",
                "MCAutoDepMods.window.main.menu.file.reload": "Reload",
                "MCAutoDepMods.window.main.menu.config": "Settings",
                "MCAutoDepMods.window.main.menu.config.language": "Language settings",
                "MCAutoDepMods.window.main.menu.help": "Help",
                "MCAutoDepMods.window.main.msg.title": "[Search directory] {mods_dir}\n[Found JAR file(s)] {file_count}\n[Missing dependencies] {missing_dep_count}(Breakdown  fabric:{fabric_count}, neoforge:{neoforge_count})\n",
                "MCAutoDepMods.window.main.msg.loader.list.title": "\n{loader} x{count}",
                "MCAutoDepMods.window.main.msg.loader.list.item": "\n|- [{loader}] {dep}  [version] {version}\n|",
                "MCAutoDepMods.window.main.msg.loader.list.end": "__\n",
                "MCAutoDepMods.window.open_dir.title": "Select the mods directory",
                "MCAutoDepMods.window.error.title": "MCAutoDepMods -ERROR",
                "MCAutoDepMods.window.error.msg.title": "Please copy this error and send it to the developer.",
                "MCAutoDepMods.window.error.msg.text.load_error": "An error occurred while loding {file}",
                "MCAutoDepMods.window.error.msg.text.read_error": "An error occurred while retrieving infomation form {file}"
            }
        }
    
    def tr(self, key, **kwargs):
        return self.translations[self.current_lang].get(key, key).format(**kwargs)

    def get_mod_info(self, jar_path):
        error_list = []
        error = False
        with zipfile.ZipFile(jar_path, "r") as jar:
            names = jar.namelist()
            
            # fabric
            if "fabric.mod.json" in names:
                with jar.open("fabric.mod.json") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        error_list.append({"loader": "fabric", "fp": jar_path, "msg": self.tr("MCAutoDepMods.window.error.msg.text.load_error", file="fabric.mod.json"), "error":e})
                        error = True
                    if not error:
                        try:
                            depends = data.get("depends", None)
                            if not depends is None:
                                for i in self.EXCLUDE_DEPENDS:
                                    depends.pop(i, None)
                            mod_id = [data["id"]]
                            provides = data.get("provides", None)
                            if not provides is None:
                                for i in provides:
                                    mod_id.append(i)
                            return "fabric", {"mod": {"id":mod_id, "ver":data["version"]}, "path": jar_path, "depends": depends}, error_list
                        except Exception as e:
                            error_list.append({"loader": "fabric", "fp": jar_path, "msg": self.tr("MCAutoDepMods.window.error.msg.text.read_error", file="fabric.mod.json"), "error":e})
                            error = True
            
            # neoforge
            toml_path = "META-INF/neoforge.mods.toml"
            if toml_path in names:
                with jar.open(toml_path) as f:
                    try:
                        data = tomllib.load(f)
                    except Exception as e:
                        error_list.append({"loader": "neoforge", "fp": jar_path, "msg": self.tr("MCAutoDepMods.window.error.msg.text.load_error", file="META-INF/neoforge.mods.toml"), "error":e})
                        error = True
                    if not error:
                        try:
                            mod_id = {"id":data["mods"][0]["modId"], "ver":data["mods"][0]["version"]}
                            if data["dependencies"][mod_id["id"]]:
                                raw_depends = data["dependencies"][mod_id["id"]]
                            if raw_depends:
                                depends = []
                                for i in raw_depends:
                                    if not i["modId"] in self.EXCLUDE_DEPENDS:
                                        if "versionRange" in i:
                                            if "type" in i:
                                                if not i["type"].lower() == "required":
                                                    continue
                                            depends.append({i["modId"]:i["versionRange"]})
                            return "neoforge", {"mod": mod_id, "jar_path": jar_path, "depends": depends}, error_list
                        except Exception as e:
                            error_list.append({"loader": "neoforge", "fp": jar_path, "msg": self.tr("MCAutoDepMods.window.error.msg.text.read_error", file="META-INF/neoforge.mods.toml"), "error":e})
                            error = True
        
        return None, None, error_list

    def fabric_version(self, depends, loaded_mods):
        for dep_id, required_version in depends.items():
            matched_mod = next((mod for mod in loaded_mods if dep_id in mod["id"]), None)
            if not matched_mod:
                return False
            actual_version = matched_mod["ver"]
            if required_version.strip() == "*":
                continue
            try:
                spec = SpecifierSet(required_version.replace(" ", ", "))
                if Version(actual_version) not in spec:
                    return False
            except Exception:
                return False
        return True

    def neoforge_version(self, depends, loaded_mods):
        def version_matches(actual_version, requird_range):
            if requird_range.strip() == "*" or requird_range.strip() == "":
                return True
            if re.fullmatch(r"\d+", requird_range):
                return actual_version == requird_range
            m = re.fullmatch(r"([\[\(])\s*([^\s,]*)\s*,\s*([^\s\]]*)\s*([\]\)])", requird_range)
            if not m:
                return False
            
            left_inclusive = m.group(1) == "["
            right_inclusive = m.group(4) == "]"
            left_ver_str = m.group(2)
            right_ver_str = m.group(3)
            
            try:
                actual = Version(actual_version)
            except Exception:
                return False
            
            if left_ver_str != "":
                try:
                    left_ver = Version(left_ver_str)
                except Exception:
                    return False
                if left_inclusive and actual < left_ver:
                    return False
                if not right_inclusive and actual <= left_ver:
                    return False
            if right_ver_str != "":
                try:
                    right_ver = Version(right_ver_str)
                except Exception:
                    return False
                if right_inclusive and actual > right_ver:
                    return False
                if not right_inclusive and actual >= right_ver:
                    return False
            return True
        for modid, ver_spec in depends.items():
            mod = next((m for m in loaded_mods if modid in m["id"]), None)
            if not mod:
                return False
            if not version_matches(mod["ver"], ver_spec):
                return False
        return True


    


    def refresh_text(self):
        missing_dep = self.result_data["missing_dep"]
        mods_fp = ["mods_fp"]
        
        if missing_dep and mods_fp:
            self.output_text_box.configure(state="normal")
            
            self.output_text_box.delete("1.0", tk.END)
            
            message = self.tr("MCAutoDepMods.window.main.msg.title", mods_dir=self.mods_dir, file_count=len(mods_fp), missing_dep_count=(len(missing_dep['fabric'])+len(missing_dep['neoforge'])), fabric_count=len(missing_dep['fabric']), neoforge_count=len(missing_dep['neoforge']))
            self.output_text_box.insert(tk.END, message)
            
            if len(missing_dep["fabric"]):
                self.output_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.main.msg.loader.list.title", loader="fabric", count=len(missing_dep["fabric"])))
                for i in missing_dep["fabric"]:
                    self.output_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.main.msg.loader.list.item", loader="fabric", dep=next(iter(i)), version=next(iter(i.values()))))
                self.output_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.main.msg.loader.list.end"))
            
            if len(missing_dep["neoforge"]):
                self.output_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.main.msg.loader.list.title", loader="neoforge", count=len(missing_dep["neoforge"])))
                for i in missing_dep["neoforge"]:
                    self.output_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.main.msg.loader.list.item", loader="neoforge", dep=next(iter(i)), version=next(iter(i.values()))))
                self.output_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.main.msg.loader.list.end"))
            
            self.output_text_box.configure(state="disabled")


    def open_mods_dir(self):
        self.mods_dir = tkf.askdirectory(title=self.tr("MCAutoDepMods.window.open_dir.title"))
        if self.mods_dir:
            self.load_mods_dir()

    def load_mods_dir(self):
        if self.mods_dir:
            mods_fp = glob.glob(os.path.join(self.mods_dir, "*.jar"))
            error_list = []
            dep_dict = {"fabric_mods": [], "fabric_dep": [], "neoforge_mods": [], "neoforge_dep": []}
            for fp in mods_fp:
                loader, data, error = self.get_mod_info(fp)
                if error:
                    for e in error:
                        error_list.append(e)
                if loader is None:
                    continue
                if loader in "fabric":
                    dep_dict["fabric_mods"].append(data["mod"])
                    if not data["depends"] is None:
                        for i in data["depends"]:
                            dep_dict["fabric_dep"].append({i:data["depends"][i]})
                elif loader in "neoforge":
                    dep_dict["neoforge_mods"].append(data["mod"])
                    if not data["depends"] is None:
                        for i in data["depends"]:
                            dep_dict["neoforge_dep"].append(i)
            
            missing_dep = {"fabric": [], "neoforge": []}
            if len(dep_dict["fabric_mods"]) >= 1:
                for i in dep_dict["fabric_dep"]:
                    if not self.fabric_version(i, dep_dict["fabric_mods"]):
                        missing_dep["fabric"].append(i)
            if len(dep_dict["neoforge_mods"]) >= 1:
                for i in dep_dict["neoforge_dep"]:
                    if not self.neoforge_version(i, dep_dict["neoforge_mods"]):
                        missing_dep["neoforge"].append(i)
            
            if error_list:
                error_msg = ""
                for i in error_list:
                    error_msg += f"[{i["loader"]}] {i["msg"]}\n{i["fp"]}\n{"-"*50}\n{i["error"]}\n{"-"*50}\n"
                self.error_msg_window(error_msg)
            else:
                self.destroy_error_msg_window()
            
            self.result_data["missing_dep"] = missing_dep
            self.result_data["mods_fp"] = mods_fp
            
            self.refresh_text()
            
        else:
            self.open_mods_dir()
    
    def error_msg_window(self, error_msg):
        if self.error_toplevel is None or not self.error_toplevel.winfo_exists():
            self.error_toplevel = tk.Toplevel(master=root)
            self.error_toplevel.title(self.tr("MCAutoDepMods.window.error.title"))
            self.error_toplevel_frame = tk.Frame(master=self.error_toplevel)
            self.error_toplevel_scrollbar = tk.Scrollbar(master=self.error_toplevel_frame)
            self.error_toplevel_text_box = tk.Text(master=self.error_toplevel_frame, state="normal", yscrollcommand=self.error_toplevel_scrollbar.set)
            self.error_toplevel_frame.pack(fill="both", expand=True)
            self.error_toplevel_scrollbar.pack(side="right", fill="y")
            self.error_toplevel_text_box.pack(side="left", fill="both", expand=True)
        
        
        self.error_toplevel_text_box.configure(state="normal")
        self.error_toplevel_text_box.delete("1.0", tk.END)
        self.error_toplevel_text_box.insert(tk.END, self.tr("MCAutoDepMods.window.error.msg.title") + "\n\n" + error_msg)
        self.error_toplevel_text_box.configure(state="disabled")
        
        self.error_toplevel.deiconify()
        self.error_toplevel.lift()
        self.error_toplevel.focus_force()
    
    def destroy_error_msg_window(self):
        if not self.error_toplevel is None and self.error_toplevel.winfo_exists():
            self.error_toplevel.destroy()
            self.error_toplevel = None



root = tk.Tk()
main = Main(root)
root.mainloop()
