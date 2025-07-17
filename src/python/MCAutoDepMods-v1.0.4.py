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


mods_dir = ""

EXCLUDE_DEPENDS = ["minecraft", "java", "fabricloader", "neoforge"]

root = tk.Tk()
root.title("MCAutoDepMods")

def get_mod_info(jar_path):
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
                    error_list.append({"loader": "fabric", "fp": jar_path, "msg": f"fabric.mod.jsonの読み込み中にエラーが発生しました", "error":e})
                    error = True
                if not error:
                    try:
                        depends = data.get("depends", None)
                        if not depends is None:
                            for i in EXCLUDE_DEPENDS:
                                depends.pop(i, None)
                        mod_id = [data["id"]]
                        provides = data.get("provides", None)
                        if not provides is None:
                            for i in provides:
                                mod_id.append(i)
                        return "fabric", {"mod": {"id":mod_id, "ver":data["version"]}, "path": jar_path, "depends": depends}, error_list
                    except Exception as e:
                        error_list.append({"loader": "fabric", "fp": jar_path, "msg": f"fabric.mod.jsonから情報取得中にエラーが発生しました", "error":e})
                        error = True
        
        # neoforge
        toml_path = "META-INF/neoforge.mods.toml"
        if toml_path in names:
            with jar.open(toml_path) as f:
                try:
                    data = tomllib.load(f)
                except Exception as e:
                    error_list.append({"loader": "neoforge", "fp": jar_path, "msg": f"META-INF/neoforge.mods.tomlの読み込み中にエラーが発生しました", "error":e})
                    error = True
                if not error:
                    try:
                        mod_id = {"id":data["mods"][0]["modId"], "ver":data["mods"][0]["version"]}
                        if data["dependencies"][mod_id["id"]]:
                            raw_depends = data["dependencies"][mod_id["id"]]
                        if raw_depends:
                            depends = []
                            for i in raw_depends:
                                if not i["modId"] in EXCLUDE_DEPENDS:
                                    if "versionRange" in i:
                                        if "type" in i:
                                            if not i["type"].lower() == "required":
                                                continue
                                        depends.append({i["modId"]:i["versionRange"]})
                        return "neoforge", {"mod": mod_id, "jar_path": jar_path, "depends": depends}, error_list
                    except Exception as e:
                        error_list.append({"loader": "neoforge", "fp": jar_path, "msg": f"META-INF/neoforge.mods.tomlから情報取得中にエラーが発生しました", "error":e})
                        error = True
    
    return None, None, error_list

def fabric_version(depends, loaded_mods):
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

def neoforge_version(depends, loaded_mods):
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


output_frame = tk.Frame(master=root)

output_text_scrollbar = tk.Scrollbar(master=output_frame)

output_text_box = tk.Text(master=output_frame,state="disabled",yscrollcommand=output_text_scrollbar.set)

output_text_scrollbar.config(command=output_text_box.yview)


def open_mods_dir():
    global mods_dir
    mods_dir = tkf.askdirectory(title="modsディレクトリを選択")
    load_mods_dir()

def load_mods_dir():
    if mods_dir:
        mods_fp = glob.glob(os.path.join(mods_dir, "*.jar"))
        error_list = []
        dep_dict = {"fabric_mods": [], "fabric_dep": [], "neoforge_mods": [], "neoforge_dep": []}
        for fp in mods_fp:
            loader, data, error = get_mod_info(fp)
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
                if not fabric_version(i, dep_dict["fabric_mods"]):
                    missing_dep["fabric"].append(i)
        if len(dep_dict["neoforge_mods"]) >= 1:
            for i in dep_dict["neoforge_dep"]:
                if not neoforge_version(i, dep_dict["neoforge_mods"]):
                    missing_dep["neoforge"].append(i)
        
        if error_list:
            msg_toplevel = tk.Toplevel(master=root)
            msg_toplevel.title("MCAutoDepMods -ERROR")
            msg_toplevel_frame = tk.Frame(master=msg_toplevel)
            msg_toplevel_text_box = tk.Text(master=msg_toplevel_frame,state="normal")
            msg_toplevel_frame.pack(fill="both", expand=True)
            msg_toplevel_text_box.pack(fill="both", expand=True)
            error_msg = "このエラーをコピーし開発者に渡してください。\n\n"
            for i in error_list:
                error_msg += f"[{i["loader"]}] {i["msg"]}\n{i["fp"]}\n{"-"*50}\n{i["error"]}\n{"-"*50}\n"
            msg_toplevel_text_box.insert(tk.END, error_msg)
            msg_toplevel_text_box.configure(state="disabled")
        
        output_text_box.configure(state="normal")
        
        output_text_box.delete("1.0", tk.END)
        
        message = f"""
[検索先ディレクトリ] {mods_dir}
[見つかったjarファイル] {len(mods_fp)}個
[見つからなかった依存関係] {(len(missing_dep['fabric'])+len(missing_dep['neoforge']))}個(内訳  fabric:{len(missing_dep['fabric'])}, neoforge:{len(missing_dep['neoforge'])})
"""
        output_text_box.insert(tk.END, message)
        
        if len(missing_dep["fabric"]):
            output_text_box.insert(tk.END, f"\nfabric x{len(missing_dep["fabric"])}")
            for i in missing_dep["fabric"]:
                output_text_box.insert(tk.END, f"\n|- [fabric] {next(iter(i))}  [version] {next(iter(i.values()))}\n|")
            output_text_box.insert(tk.END, "__\n")
        
        if len(missing_dep["neoforge"]):
            output_text_box.insert(tk.END, f"\nneoforge x{len(missing_dep["neoforge"])}")
            for i in missing_dep["neoforge"]:
                output_text_box.insert(tk.END, f"\n|- [neoforge] {next(iter(i))}  [version] {next(iter(i.values()))}\n|")
            output_text_box.insert(tk.END, "__\n")
        
        output_text_box.configure(state="disabled")
    else:
        open_mods_dir()


mods_button_frame = tk.Frame(master=root)
mods_select_button = tk.Button(master=mods_button_frame, text="modsディレクトリを選択", command=open_mods_dir)
mods_reload_button = tk.Button(master=mods_button_frame, text="リロード", command=load_mods_dir)

mods_button_frame.pack()
mods_select_button.pack(side="left")
mods_reload_button.pack(side="right")
output_frame.pack(fill="both", expand=True)
output_text_scrollbar.pack(side="right", fill="y")
output_text_box.pack(side="left", fill="both", expand=True)



root.mainloop()
