import torch
import gc

def aggressive_cleanup():
    """Shared memory cleanup for 8GB VRAM optimization."""
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        try:
            torch.cuda.ipc_collect()
        except:
            pass