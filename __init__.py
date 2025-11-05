import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel, PropertyGroup
import os

bl_info = {
    "name": "_ Unity. FBX Exporter for Unity",
    "author": "Yame",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Unity Tools",
    "description": "Exports selected meshes and armatures as FBX compatible with Unity",
    "category": "3D View",
}

# プロパティを格納するクラス
class FolderSelectProperties(PropertyGroup):
    folder_path: StringProperty(
        name="Folder Path",
        description="Selected folder path",
        default="",
        subtype="DIR_PATH",
    )

LANG_OPTIONS = [
    ("JP", "JP", "日本語表示"),
    ("EN", "EN", "English display"),
]

def get_default_filename():
    try:
        path = bpy.data.filepath
        if path:
            return os.path.splitext(os.path.basename(path))[0]
    except AttributeError:
        pass
    return "exported_model"

def init_props():
    bpy.types.Scene.unity_fbx_filename = bpy.props.StringProperty(
        name="File Name",
        default="UnsavedFile"
    )
    # デフォルトを日本語表示 (次に切り替えるのは英語なのでボタンは EN )
    bpy.types.Scene.ui_lang = bpy.props.EnumProperty(
        name="Language",
        items=LANG_OPTIONS,
        default="JP"
    )
    bpy.types.Scene.folder_select_props = bpy.props.PointerProperty(type=FolderSelectProperties)

# フォルダ選択用オペレーター
class OT_SelectFolder(Operator):
    bl_idname = "wm.select_folder_example"
    bl_label = "Select Folder"
    bl_description = "Open file browser to select a folder"

    directory: StringProperty(
        name="Directory",
        description="Path to selected directory",
        subtype='DIR_PATH'
    )

    def invoke(self, context, event):
        # フォルダ選択ダイアログを開く
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = context.scene.folder_select_props
        props.folder_path = self.directory
        self.report({'INFO'}, f"Selected Folder: {self.directory}")
        return {'FINISHED'}

def clear_props():
    del bpy.types.Scene.unity_fbx_filename
    del bpy.types.Scene.ui_lang


# --- 言語切替オペレーター ---
class UNITY_OT_ToggleLang(bpy.types.Operator):
    """言語を切り替える"""
    bl_idname = "unity.toggle_lang"
    bl_label = "Toggle Language"

    def execute(self, context):
        scene = context.scene
        scene.ui_lang = "EN" if scene.ui_lang == "JP" else "JP"
        return {'FINISHED'}


# --- Rボタン用オペレーター ---
class UNITY_OT_ResetFileName(bpy.types.Operator):
    """現在の .blend ファイル名をセット"""
    bl_idname = "unity.reset_filename"
    bl_label = "R"

    def execute(self, context):
        scene = context.scene
        scene.unity_fbx_filename = get_default_filename()
        self.report({'INFO'}, f"File name reset to {scene.unity_fbx_filename}")
        return {'FINISHED'}


# --- FBX出力オペレーター ---
class UNITY_OT_ExportFBX(bpy.types.Operator):
    bl_idname = "unity.export_fbx"
    bl_label = "Export FBX for Unity"

    def execute(self, context):
        scene = context.scene
        props = scene.folder_select_props
        filename = scene.unity_fbx_filename.strip()
        if not filename:
            self.report({'WARNING'}, "File name is empty")
            return {'CANCELLED'}

        # フォルダが未指定なら blendファイルのパスを使う
        folder = props.folder_path.strip()
        if not folder:
            folder = bpy.path.abspath("//")

        # 出力フルパス
        # output_path = os.path.join(bpy.path.abspath("//"), filename + ".fbx")
        output_path = os.path.join(bpy.path.abspath(folder), filename + ".fbx")

        bpy.ops.export_scene.fbx(
            filepath=output_path,
#            use_selection=True,
            use_visible=True,
            object_types={'ARMATURE', 'MESH', 'EMPTY'},
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_UNITS',
            global_scale=1.0,  # Custom Scale を使う場合に変更
#            filepath="", check_existing=True, filter_glob="*.fbx", use_selection=False, use_visible=False
#            , use_active_collection=False, collection="", global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE'
#            , use_space_transform=True, bake_space_transform=False
#            , object_types={'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'}
#            , use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='OFF', colors_type='SRGB'
#            , prioritize_active_color=False, use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_triangles=False
#            , use_custom_props=False, add_leaf_bones=True, primary_bone_axis='Y', secondary_bone_axis='X'
#            , use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_bones=True
#            , bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True
#            , bake_anim_step=1, bake_anim_simplify_factor=1, path_mode='AUTO', embed_textures=False, batch_mode='OFF'
#            , use_batch_own_dir=True, use_metadata=True, axis_forward='-Z', axis_up='Y')
        )
        self.report({'INFO'}, f"Exported FBX to {output_path}")
        return {'FINISHED'}


# --- パネル ---
class UNITY_PT_ExporterPanel(bpy.types.Panel):
    bl_label = "Unity FBX Exporter"
    bl_idname = "UNITY_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # 次に切り替わる言語を表示（JP→EN / EN→JP）
        next_label = "EN" if scene.ui_lang == "JP" else "JP"

        row = layout.row(align=True)
        row.scale_x = 0.2  # 横幅を半分に
        row.operator("unity.toggle_lang", text=next_label)

        # ★ emboss=False で小さめボタン
#        op = row.operator("unity.toggle_lang", text=next_label, emboss=False)
        row.scale_x = 1.5  # ラベルとボタンを同じ行に置く場合の横幅を拡大

        # 言語に応じて表示切替
        label_text = (
            "Unity用FBXとしてエクスポート"
            if scene.ui_lang == "JP"
            else "Export selected objects as FBX for Unity"
        )
        row.label(text=label_text)

        # フォルダパスとダイアログボタン
        props = context.scene.folder_select_props
        layout.prop(props, "folder_path", text="")

        # ファイル名入力とRボタン
        row = layout.row(align=True)
        row.scale_x = 1.5  # ラベルとボタンを同じ行に置く場合の横幅を拡大
        row.prop(scene, "unity_fbx_filename", text="")
        row.scale_x = 0.2  # 横幅を半分に
        row.label(text=".fbx")
        row.operator("unity.reset_filename", text="R")

        layout.operator("unity.export_fbx", icon='EXPORT')


# 登録処理
classes = [
    UNITY_OT_ExportFBX,
    UNITY_OT_ToggleLang,
    UNITY_OT_ResetFileName,
    UNITY_PT_ExporterPanel,
    FolderSelectProperties,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    init_props()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    clear_props()

if __name__ == "__main__":
    register()
