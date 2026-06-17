import os

meshes_folder = "./meshes"
sdf_output = "model.sdf"
model_name = "amr_inspection_facility"

with open(sdf_output, "w") as f:
    f.write(f'<?xml version="1.0"?>\n<sdf version="1.9">\n  <model name="{model_name}">\n    <static>true</static>\n\n')
    
    # ترتيب الملفات أبجدياً
    for filename in sorted(os.listdir(meshes_folder)):
        # التأكد من أخذ ملفات الـ OBJ فقط (وتجاهل ملفات الـ MTL)
        if filename.endswith(".obj"):
            name = filename.replace(".obj", "")
            f.write(f'    <link name="{name}_link">\n')
            f.write(f'      <visual name="visual">\n        <geometry>\n          <mesh><uri>model://{model_name}/meshes/{filename}</uri></mesh>\n        </geometry>\n      </visual>\n')
            f.write(f'      <collision name="collision">\n        <geometry>\n          <mesh><uri>model://{model_name}/meshes/{filename}</uri></mesh>\n        </geometry>\n      </collision>\n    </link>\n\n')
            
    f.write('  </model>\n</sdf>')

print("تم إنشاء ملف الـ model.sdf بنجاح كـ Links بصيغة OBJ!")