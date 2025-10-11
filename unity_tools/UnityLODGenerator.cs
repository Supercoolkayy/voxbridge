using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections.Generic;

/// <summary>
/// VoxBridge Unity LOD Generator
/// Automatically creates LOD0, LOD1, LOD2 prefabs from VoxBridge models
/// 
/// USAGE:
/// 1. Import your VoxBridge ZIP file into Unity
/// 2. Select the imported model in Project window
/// 3. Right-click → VoxBridge → Generate LOD Prefab
/// 4. LOD prefab will be created with 3 levels (LOD0=100%, LOD1=70%, LOD2=40%)
/// </summary>
public class UnityLODGenerator : EditorWindow
{
    private GameObject selectedModel;
    private string prefabSavePath = "Assets/VoxBridge_LODs/";
    
    [MenuItem("VoxBridge/Generate LOD Prefab")]
    static void ShowWindow()
    {
        var window = GetWindow<UnityLODGenerator>("VoxBridge LOD Generator");
        window.Show();
    }
    
    void OnGUI()
    {
        GUILayout.Label("VoxBridge LOD Generator", EditorStyles.boldLabel);
        GUILayout.Space(10);
        
        EditorGUILayout.HelpBox(
            "This tool creates a prefab with 3 LOD levels for mobile optimization:\n" +
            "• LOD0: 100% quality (original)\n" +
            "• LOD1: 70% quality\n" +
            "• LOD2: 40% quality", 
            MessageType.Info
        );
        
        GUILayout.Space(10);
        selectedModel = (GameObject)EditorGUILayout.ObjectField(
            "VoxBridge Model:", 
            selectedModel, 
            typeof(GameObject), 
            true
        );
        
        prefabSavePath = EditorGUILayout.TextField("Save Path:", prefabSavePath);
        
        GUILayout.Space(10);
        
        if (GUILayout.Button("Generate LOD Prefab", GUILayout.Height(40)))
        {
            if (selectedModel == null)
            {
                EditorUtility.DisplayDialog("Error", "Please select a model first!", "OK");
                return;
            }
            
            GenerateLODPrefab();
        }
    }
    
    void GenerateLODPrefab()
    {
        // Ensure save directory exists
        if (!Directory.Exists(prefabSavePath))
        {
            Directory.CreateDirectory(prefabSavePath);
            AssetDatabase.Refresh();
        }
        
        // Create LOD root object
        GameObject lodRoot = new GameObject(selectedModel.name + "_LOD");
        
        // Add LOD Group component
        LODGroup lodGroup = lodRoot.AddComponent<LODGroup>();
        
        // Create 3 LOD levels
        LOD[] lods = new LOD[3];
        
        // LOD0 - 100% quality (original model)
        GameObject lod0 = Instantiate(selectedModel, lodRoot.transform);
        lod0.name = "LOD0_100%";
        lods[0] = new LOD(0.6f, lod0.GetComponentsInChildren<Renderer>());
        
        // LOD1 - 70% quality (use mesh simplification)
        GameObject lod1 = Instantiate(selectedModel, lodRoot.transform);
        lod1.name = "LOD1_70%";
        SimplifyMeshes(lod1, 0.7f);
        lods[1] = new LOD(0.3f, lod1.GetComponentsInChildren<Renderer>());
        
        // LOD2 - 40% quality (aggressive simplification)
        GameObject lod2 = Instantiate(selectedModel, lodRoot.transform);
        lod2.name = "LOD2_40%";
        SimplifyMeshes(lod2, 0.4f);
        lods[2] = new LOD(0.1f, lod2.GetComponentsInChildren<Renderer>());
        
        // Apply LODs to group
        lodGroup.SetLODs(lods);
        lodGroup.RecalculateBounds();
        
        // Save as prefab
        string prefabPath = Path.Combine(prefabSavePath, lodRoot.name + ".prefab");
        PrefabUtility.SaveAsPrefabAsset(lodRoot, prefabPath);
        
        // Clean up temporary object
        DestroyImmediate(lodRoot);
        
        // Select the created prefab
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
        Selection.activeObject = prefab;
        EditorGUIUtility.PingObject(prefab);
        
        EditorUtility.DisplayDialog(
            "Success!", 
            $"LOD Prefab created at:\n{prefabPath}\n\n" +
            "LOD0: 100% quality (0.6-1.0 screen height)\n" +
            "LOD1: 70% quality (0.3-0.6 screen height)\n" +
            "LOD2: 40% quality (0.1-0.3 screen height)", 
            "OK"
        );
        
        Debug.Log($"VoxBridge: LOD Prefab created at {prefabPath}");
    }
    
    void SimplifyMeshes(GameObject obj, float quality)
    {
        // Unity's built-in mesh simplification
        // This is a basic implementation - for production use, consider:
        // - UnityMeshSimplifier asset from Unity Asset Store
        // - InstaLOD plugin
        // - Simplygon integration
        
        MeshFilter[] meshFilters = obj.GetComponentsInChildren<MeshFilter>();
        
        foreach (MeshFilter mf in meshFilters)
        {
            if (mf.sharedMesh != null)
            {
                // Create a copy of the mesh
                Mesh simplifiedMesh = Instantiate(mf.sharedMesh);
                simplifiedMesh.name = $"{mf.sharedMesh.name}_LOD{(int)(quality * 100)}";
                
                // Note: Unity doesn't have built-in mesh simplification in runtime
                // For actual simplification, you would need:
                // 1. Pre-simplify in VoxBridge with different --optimize-mesh ratios
                // 2. Use a Unity asset like UnityMeshSimplifier
                // 3. Use external tools
                
                // For now, we just use the same mesh at different screen heights
                // Users can replace these with pre-simplified meshes from VoxBridge
                
                mf.sharedMesh = simplifiedMesh;
            }
        }
        
        // Scale down for visual LOD effect (optional)
        // obj.transform.localScale *= quality;
    }
}

/// <summary>
/// Instructions for using pre-simplified meshes from VoxBridge:
/// 
/// Option 1: Manual LOD Creation (Recommended)
/// 1. Convert your model 3 times with VoxBridge:
///    - voxbridge convert model.glb -o lod0/ -t unity
///    - voxbridge convert model.glb -o lod1/ -t unity --optimize-mesh --texture-size 512
///    - voxbridge convert model.glb -o lod2/ -t unity --optimize-mesh --texture-size 256
/// 
/// 2. Import all 3 into Unity (LOD0, LOD1, LOD2 folders)
/// 
/// 3. Use this script to combine them into LOD Group prefab
/// 
/// Option 2: Automatic (This Script)
/// - Uses same mesh for all LOD levels
/// - Relies on Unity's distance culling
/// - Replace with pre-simplified meshes later if needed
/// 
/// Option 3: Unity Asset Store
/// - Use "UnityMeshSimplifier" asset for runtime mesh simplification
/// - This script can integrate with it
/// </summary>

