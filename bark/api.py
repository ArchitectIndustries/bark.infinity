from typing import Optional
import multiprocessing
import numpy as np
import torch
from .generation import codec_decode, generate_coarse, generate_fine, generate_text_semantic


def text_to_semantic(
    text: str,
    history_prompt: Optional[str] = None,
    temp: float = 0.7,
    use_gpu = True,
    base = None,
    confused_travolta_mode = False,
):
    """Generate semantic array from text.

    Args:
        text: text to be turned into audio
        history_prompt: history choice for audio cloning
        temp: generation temperature (1.0 more diverse, 0.0 more conservative)

    Returns:
        numpy semantic array to be fed into `semantic_to_waveform`
    """
    allow_early_stop = not confused_travolta_mode
    
    x_semantic = generate_text_semantic(
        text,
        history_prompt=history_prompt,
        temp=temp,
        use_gpu=use_gpu,
        base=base,
        allow_early_stop=allow_early_stop,
    )
    return x_semantic


def semantic_to_waveform(
    semantic_tokens: np.ndarray,
    history_prompt: Optional[str] = None,
    temp: float = 0.7,
    use_gpu_for_all_steps = True,
    base=None,
):
    """Generate audio array from semantic input.

    Args:
        semantic_tokens: semantic token output from `text_to_semantic`
        history_prompt: history choice for audio cloning
        temp: generation temperature (1.0 more diverse, 0.0 more conservative)

    Returns:
        numpy audio array at sample frequency 24khz
    """
    x_coarse_gen = generate_coarse(
        semantic_tokens,
        history_prompt=history_prompt,
        temp=temp,
        use_gpu=True,
        base=base,
    )
    x_fine_gen = generate_fine(
        x_coarse_gen,
        history_prompt=history_prompt,
        temp=0.5,
        use_gpu=use_gpu_for_all_steps,
        base=base,
    )
    audio_arr = codec_decode(x_fine_gen, use_gpu=use_gpu_for_all_steps)
    return audio_arr, x_coarse_gen, x_fine_gen


def generate_audio(
    text: str,
    history_prompt: Optional[str] = None,
    text_temp: float = 0.7,
    waveform_temp: float = 0.7,
    use_gpu_for_all_steps = True,
    base = None,
    confused_travolta_mode = False,
):
    """Generate audio array from input text.

    Args:
        text: text to be turned into audio
        history_prompt: history choice for audio cloning
        text_temp: generation temperature (1.0 more diverse, 0.0 more conservative)
        waveform_temp: generation temperature (1.0 more diverse, 0.0 more conservative)

    Returns:
        numpy audio array at sample frequency 24khz
    """

    torch.set_num_threads(multiprocessing.cpu_count())

    x_semantic = text_to_semantic(text, history_prompt=history_prompt, temp=text_temp, use_gpu=use_gpu_for_all_steps, base=base, confused_travolta_mode=confused_travolta_mode)
    audio_arr, c, f = semantic_to_waveform(x_semantic, history_prompt=history_prompt, temp=waveform_temp, use_gpu_for_all_steps=use_gpu_for_all_steps, base=base)
    return audio_arr, [x_semantic, c, f]
