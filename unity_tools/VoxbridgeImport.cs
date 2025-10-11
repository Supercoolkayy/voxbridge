using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections.Generic;
using System.Linq;

/// <summary>
/// VoxBridge Unity Import Script
/// Automatically sets up animations and materials for VoxBridge-exported models
/// </summary>
[System.Serializable]
public class VoxbridgeImport : AssetPostprocessor
{
    private static readonly string VOXBRIDGE_MARKER = "VoxBridge";
    
    void OnPreprocessModel()
    {
        // Check if this is a VoxBridge model
        if (IsVoxbridgeModel(assetImporter.assetPath))
        {
            Debug.Log($"VoxBridge: Processing {assetImporter.assetPath}");
            
            // Configure model import settings for VoxBridge models
            ModelImporter modelImporter = assetImporter as ModelImporter;
            if (modelImporter != null)
            {
                // Enable animations
                modelImporter.importAnimation = true;
                modelImporter.animationType = ModelImporterAnimationType.Generic;
                
                // Optimize for VoxBridge exports
                modelImporter.optimizeMesh = true;
                modelImporter.optimizeGameObjects = true;
                
                // Ensure proper material import
                modelImporter.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
                modelImporter.materialLocation = ModelImporterMaterialLocation.InPrefab;
            }
        }
    }
    
    void OnPostprocessModel(GameObject g)
    {
        if (IsVoxbridgeModel(assetImporter.assetPath))
        {
            Debug.Log($"VoxBridge: Post-processing {g.name}");
            
            // Auto-setup animations
            SetupAnimations(g);
            
            // Auto-setup materials
            SetupMaterials(g);
            
            // Add VoxBridge component for identification
            VoxbridgeModelInfo info = g.AddComponent<VoxbridgeModelInfo>();
            info.originalPath = assetImporter.assetPath;
            info.importTime = System.DateTime.Now;
        }
    }
    
    private bool IsVoxbridgeModel(string assetPath)
    {
        // Check if the GLTF file contains VoxBridge metadata
        if (assetPath.EndsWith(".gltf") || assetPath.EndsWith(".glb"))
        {
            try
            {
                string content = File.ReadAllText(assetPath);
                return content.Contains(VOXBRIDGE_MARKER) || 
                       content.Contains("VoxBridge") ||
                       Path.GetFileName(assetPath).Contains("_unity");
            }
            catch
            {
                return false;
            }
        }
        return false;
    }
    
    private void SetupAnimations(GameObject root)
    {
        // Find all animation clips
        AnimationClip[] clips = AnimationUtility.GetAnimationClips(root);
        
        if (clips.Length == 0)
        {
            Debug.Log("VoxBridge: No animation clips found");
            return;
        }
        
        Debug.Log($"VoxBridge: Found {clips.Length} animation clips");
        
        // Create Animator Controller
        string controllerPath = GetControllerPath(root.name);
        AnimatorController controller = CreateAnimatorController(controllerPath, clips);
        
        // Add Animator component
        Animator animator = root.GetComponent<Animator>();
        if (animator == null)
        {
            animator = root.AddComponent<Animator>();
        }
        
        // Assign controller
        animator.runtimeAnimatorController = controller;
        
        // Set up default state
        if (clips.Length > 0)
        {
            animator.Play(clips[0].name);
        }
        
        Debug.Log($"VoxBridge: Created Animator Controller at {controllerPath}");
    }
    
    private AnimatorController CreateAnimatorController(string path, AnimationClip[] clips)
    {
        // Create new Animator Controller
        AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(path);
        
        // Get the base layer
        AnimatorControllerLayer baseLayer = controller.layers[0];
        AnimatorStateMachine stateMachine = baseLayer.stateMachine;
        
        // Create states for each animation clip
        foreach (AnimationClip clip in clips)
        {
            AnimatorState state = stateMachine.AddState(clip.name);
            state.motion = clip;
            
            // Set as default state if it's the first clip
            if (clip == clips[0])
            {
                stateMachine.defaultState = state;
            }
        }
        
        return controller;
    }
    
    private void SetupMaterials(GameObject root)
    {
        // Find all renderers
        Renderer[] renderers = root.GetComponentsInChildren<Renderer>();
        
        foreach (Renderer renderer in renderers)
        {
            // Ensure materials are properly configured
            Material[] materials = renderer.materials;
            for (int i = 0; i < materials.Length; i++)
            {
                if (materials[i] != null)
                {
                    // Set up standard shader properties for VoxBridge materials
                    SetupMaterialProperties(materials[i]);
                }
            }
        }
        
        Debug.Log($"VoxBridge: Configured materials for {renderers.Length} renderers");
    }
    
    private void SetupMaterialProperties(Material material)
    {
        // Ensure proper shader assignment
        if (material.shader.name.Contains("Standard") || material.shader.name.Contains("URP"))
        {
            // Configure metallic-roughness properties
            if (material.HasProperty("_MetallicGlossMap"))
            {
                // VoxBridge splits metallic-roughness, so we need to handle this
                material.EnableKeyword("_METALLICGLOSSMAP");
            }
            
            // Enable normal mapping if normal texture exists
            if (material.HasProperty("_BumpMap") && material.GetTexture("_BumpMap") != null)
            {
                material.EnableKeyword("_NORMALMAP");
            }
            
            // Enable emission if emissive texture exists
            if (material.HasProperty("_EmissionMap") && material.GetTexture("_EmissionMap") != null)
            {
                material.EnableKeyword("_EMISSION");
            }
        }
    }
    
    private string GetControllerPath(string modelName)
    {
        string directory = Path.GetDirectoryName(assetImporter.assetPath);
        return Path.Combine(directory, $"{modelName}_AnimatorController.controller");
    }
}

/// <summary>
/// Component to identify VoxBridge models
/// </summary>
public class VoxbridgeModelInfo : MonoBehaviour
{
    [Header("VoxBridge Model Information")]
    public string originalPath;
    public System.DateTime importTime;
    
    void Start()
    {
        Debug.Log($"VoxBridge Model: {gameObject.name} (Imported: {importTime})");
    }
}
