import time
import inspect
from collections import namedtuple
from typing import Optional, Dict, Any
from fastapi import FastAPI
from gradio import Blocks
import modules.errors as errors


def report_exception(e, c, job):
    errors.display(e, f'executing callback: {c.script} {job}')


class ImageSaveParams:
    def __init__(self, image, p, filename, pnginfo):
        self.image = image
        """the PIL image itself"""

        self.p = p
        """p object with processing parameters; either StableDiffusionProcessing or an object with same fields"""

        self.filename = filename
        """name of file that the image would be saved to"""

        self.pnginfo = pnginfo
        """dictionary with parameters for image's PNG info data; infotext will have the key 'parameters'"""


class CFGDenoiserParams:
    def __init__(self, x, image_cond, sigma, sampling_step, total_sampling_steps, text_cond, text_uncond):
        self.x = x
        """Latent image representation in the process of being denoised"""

        self.image_cond = image_cond
        """Conditioning image"""

        self.sigma = sigma
        """Current sigma noise step value"""

        self.sampling_step = sampling_step
        """Current Sampling step number"""

        self.total_sampling_steps = total_sampling_steps
        """Total number of sampling steps planned"""

        self.text_cond = text_cond
        """ Encoder hidden states of text conditioning from prompt"""

        self.text_uncond = text_uncond
        """ Encoder hidden states of text conditioning from negative prompt"""


class CFGDenoisedParams:
    def __init__(self, x, sampling_step, total_sampling_steps, inner_model):
        self.x = x
        """Latent image representation in the process of being denoised"""

        self.sampling_step = sampling_step
        """Current Sampling step number"""

        self.total_sampling_steps = total_sampling_steps
        """Total number of sampling steps planned"""

        self.inner_model = inner_model
        """Inner model reference used for denoising"""


class AfterCFGCallbackParams:
    def __init__(self, x, sampling_step, total_sampling_steps):
        self.x = x
        """Latent image representation in the process of being denoised"""

        self.sampling_step = sampling_step
        """Current Sampling step number"""

        self.total_sampling_steps = total_sampling_steps
        """Total number of sampling steps planned"""


class UiTrainTabParams:
    def __init__(self, txt2img_preview_params):
        self.txt2img_preview_params = txt2img_preview_params


class ImageGridLoopParams:
    def __init__(self, imgs, cols, rows):
        self.imgs = imgs
        self.cols = cols
        self.rows = rows


ScriptCallback = namedtuple("ScriptCallback", ["script", "callback"])
callback_map = dict(
    callbacks_app_started=[],
    callbacks_model_loaded=[],
    callbacks_ui_tabs=[],
    callbacks_ui_train_tabs=[],
    callbacks_ui_settings=[],
    callbacks_before_image_saved=[],
    callbacks_image_saved=[],
    callbacks_image_save_btn=[],
    callbacks_cfg_denoiser=[],
    callbacks_cfg_denoised=[],
    callbacks_cfg_after_cfg=[],
    callbacks_before_component=[],
    callbacks_after_component=[],
    callbacks_image_grid=[],
    callbacks_infotext_pasted=[],
    callbacks_script_unloaded=[],
    callbacks_before_ui=[],
    callbacks_on_reload=[],
)


def timer(t0: float, script, callback: str):
    t1 = time.time()
    s = round(t1 - t0, 2)
    if s > 0.1:
        errors.log.debug(f'Script: {s}s {callback} {script}')


def clear_callbacks():
    for callback_list in callback_map.values():
        callback_list.clear()


def app_started_callback(demo: Optional[Blocks], app: FastAPI):
    for c in callback_map['callbacks_app_started']:
        try:
            t0 = time.time()
            c.callback(demo, app)
            timer(t0, c.script, 'app_started')
        except Exception as e:
            report_exception(e, c, 'app_started_callback')


def app_reload_callback():
    for c in callback_map['callbacks_on_reload']:
        try:
            t0 = time.time()
            c.callback()
            timer(t0, c.script, 'on_reload')
        except Exception as e:
            report_exception(e, c, 'callbacks_on_reload')


def model_loaded_callback(sd_model):
    for c in callback_map['callbacks_model_loaded']:
        try:
            t0 = time.time()
            c.callback(sd_model)
            timer(t0, c.script, 'model_loaded')
        except Exception as e:
            report_exception(e, c, 'model_loaded_callback')


def ui_tabs_callback():
    res = []
    for c in callback_map['callbacks_ui_tabs']:
        try:
            t0 = time.time()
            res += c.callback() or []
            timer(t0, c.script, 'ui_tabs')
        except Exception as e:
            report_exception(e, c, 'ui_tabs_callback')
    return res


def ui_train_tabs_callback(params: UiTrainTabParams):
    for c in callback_map['callbacks_ui_train_tabs']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'ui_train_tabs')
        except Exception as e:
            report_exception(e, c, 'callbacks_ui_train_tabs')


def ui_settings_callback():
    for c in callback_map['callbacks_ui_settings']:
        try:
            t0 = time.time()
            c.callback()
            timer(t0, c.script, 'ui_settings')
        except Exception as e:
            report_exception(e, c, 'ui_settings_callback')


def before_image_saved_callback(params: ImageSaveParams):
    for c in callback_map['callbacks_before_image_saved']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'before_image_saved')
        except Exception as e:
            report_exception(e, c, 'before_image_saved_callback')


def image_saved_callback(params: ImageSaveParams):
    for c in callback_map['callbacks_image_saved']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'image_saved')
        except Exception as e:
            report_exception(e, c, 'image_saved_callback')


def image_save_btn_callback(filename: str):
    for c in callback_map['callbacks_image_save_btn']:
        try:
            t0 = time.time()
            c.callback(filename)
            timer(t0, c.script, 'image_save_btn')
        except Exception as e:
            report_exception(e, c, 'image_save_btn_callback')


def cfg_denoiser_callback(params: CFGDenoiserParams):
    for c in callback_map['callbacks_cfg_denoiser']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'cfg_denoiser')
        except Exception as e:
            report_exception(e, c, 'cfg_denoiser_callback')


def cfg_denoised_callback(params: CFGDenoisedParams):
    for c in callback_map['callbacks_cfg_denoised']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'cfg_denoised')
        except Exception as e:
            report_exception(e, c, 'cfg_denoised_callback')


def cfg_after_cfg_callback(params: AfterCFGCallbackParams):
    for c in callback_map['callbacks_cfg_after_cfg']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'cfg_after_cfg')
        except Exception as e:
            report_exception(e, c, 'cfg_after_cfg_callback')


def before_component_callback(component, **kwargs):
    for c in callback_map['callbacks_before_component']:
        try:
            t0 = time.time()
            c.callback(component, **kwargs)
            timer(t0, c.script, 'before_component')
        except Exception as e:
            report_exception(e, c, 'before_component_callback')


def after_component_callback(component, **kwargs):
    for c in callback_map['callbacks_after_component']:
        try:
            t0 = time.time()
            c.callback(component, **kwargs)
            timer(t0, c.script, 'after_component')
        except Exception as e:
            report_exception(e, c, 'after_component_callback')


def image_grid_callback(params: ImageGridLoopParams):
    for c in callback_map['callbacks_image_grid']:
        try:
            t0 = time.time()
            c.callback(params)
            timer(t0, c.script, 'image_grid')
        except Exception as e:
            report_exception(e, c, 'image_grid')


def infotext_pasted_callback(infotext: str, params: Dict[str, Any]):
    for c in callback_map['callbacks_infotext_pasted']:
        try:
            t0 = time.time()
            c.callback(infotext, params)
            timer(t0, c.script, 'infotext_pasted')
        except Exception as e:
            report_exception(e, c, 'infotext_pasted')


def script_unloaded_callback():
    for c in reversed(callback_map['callbacks_script_unloaded']):
        try:
            t0 = time.time()
            c.callback()
            timer(t0, c.script, 'script_unloaded')
        except Exception as e:
            report_exception(e, c, 'script_unloaded')


def before_ui_callback():
    for c in reversed(callback_map['callbacks_before_ui']):
        try:
            t0 = time.time()
            c.callback()
            timer(t0, c.script, 'before_ui')
        except Exception as e:
            report_exception(e, c, 'before_ui')


def add_callback(callbacks, fun):
    stack = [x for x in inspect.stack() if x.filename != __file__]
    filename = stack[0].filename if len(stack) > 0 else 'unknown file'
    callbacks.append(ScriptCallback(filename, fun))


def remove_current_script_callbacks():
    stack = [x for x in inspect.stack() if x.filename != __file__]
    filename = stack[0].filename if len(stack) > 0 else 'unknown file'
    if filename == 'unknown file':
        return
    for callback_list in callback_map.values():
        for callback_to_remove in [cb for cb in callback_list if cb.script == filename]:
            callback_list.remove(callback_to_remove)


def remove_callbacks_for_function(callback_func):
    for callback_list in callback_map.values():
        for callback_to_remove in [cb for cb in callback_list if cb.callback == callback_func]:
            callback_list.remove(callback_to_remove)


def on_app_started(callback):
    """register a function to be called when the webui started, the gradio `Block` component and
    fastapi `FastAPI` object are passed as the arguments"""
    add_callback(callback_map['callbacks_app_started'], callback)


def on_before_reload(callback):
    """register a function to be called just before the server reloads."""
    add_callback(callback_map['callbacks_on_reload'], callback)


def on_model_loaded(callback):
    """register a function to be called when the stable diffusion model is created; the model is
    passed as an argument; this function is also called when the script is reloaded. """
    add_callback(callback_map['callbacks_model_loaded'], callback)


def on_ui_tabs(callback):
    """register a function to be called when the UI is creating new tabs.
    The function must either return a None, which means no new tabs to be added, or a list, where
    each element is a tuple:
        (gradio_component, title, elem_id)

    gradio_component is a gradio component to be used for contents of the tab (usually gr.Blocks)
    title is tab text displayed to user in the UI
    elem_id is HTML id for the tab
    """
    add_callback(callback_map['callbacks_ui_tabs'], callback)


def on_ui_train_tabs(callback):
    """register a function to be called when the UI is creating new tabs for the train tab.
    Create your new tabs with gr.Tab.
    """
    add_callback(callback_map['callbacks_ui_train_tabs'], callback)


def on_ui_settings(callback):
    """register a function to be called before UI settings are populated; add your settings
    by using shared.opts.add_option(shared.OptionInfo(...)) """
    add_callback(callback_map['callbacks_ui_settings'], callback)


def on_before_image_saved(callback):
    """register a function to be called before an image is saved to a file.
    The callback is called with one argument:
        - params: ImageSaveParams - parameters the image is to be saved with. You can change fields in this object.
    """
    add_callback(callback_map['callbacks_before_image_saved'], callback)


def on_image_saved(callback):
    """register a function to be called after an image is saved to a file.
    The callback is called with one argument:
        - params: ImageSaveParams - parameters the image was saved with. Changing fields in this object does nothing.
    """
    add_callback(callback_map['callbacks_image_saved'], callback)


def on_image_save_btn(callback):
    """register a function to be called after an image save button is pressed.
    The callback is called with one argument:
        - params: ImageSaveParams - parameters the image was saved with. Changing fields in this object does nothing.
    """
    add_callback(callback_map['callbacks_image_save_btn'], callback)


def on_cfg_denoiser(callback):
    """register a function to be called in the kdiffussion cfg_denoiser method after building the inner model inputs.
    The callback is called with one argument:
        - params: CFGDenoiserParams - parameters to be passed to the inner model and sampling state details.
    """
    add_callback(callback_map['callbacks_cfg_denoiser'], callback)


def on_cfg_denoised(callback):
    """register a function to be called in the kdiffussion cfg_denoiser method after building the inner model inputs.
    The callback is called with one argument:
        - params: CFGDenoisedParams - parameters to be passed to the inner model and sampling state details.
    """
    add_callback(callback_map['callbacks_cfg_denoised'], callback)


def on_cfg_after_cfg(callback):
    """register a function to be called in the kdiffussion cfg_denoiser method after cfg calculations are completed.
    The callback is called with one argument:
        - params: AfterCFGCallbackParams - parameters to be passed to the script for post-processing after cfg calculation.
    """
    add_callback(callback_map['callbacks_cfg_after_cfg'], callback)


def on_before_component(callback):
    """register a function to be called before a component is created.
    The callback is called with arguments:
        - component - gradio component that is about to be created.
        - **kwargs - args to gradio.components.IOComponent.__init__ function

    Use elem_id/label fields of kwargs to figure out which component it is.
    This can be useful to inject your own components somewhere in the middle of vanilla UI.
    """
    add_callback(callback_map['callbacks_before_component'], callback)


def on_after_component(callback):
    """register a function to be called after a component is created. See on_before_component for more."""
    add_callback(callback_map['callbacks_after_component'], callback)


def on_image_grid(callback):
    """register a function to be called before making an image grid.
    The callback is called with one argument:
       - params: ImageGridLoopParams - parameters to be used for grid creation. Can be modified.
    """
    add_callback(callback_map['callbacks_image_grid'], callback)


def on_infotext_pasted(callback):
    """register a function to be called before applying an infotext.
    The callback is called with two arguments:
       - infotext: str - raw infotext.
       - result: Dict[str, any] - parsed infotext parameters.
    """
    add_callback(callback_map['callbacks_infotext_pasted'], callback)


def on_script_unloaded(callback):
    """register a function to be called before the script is unloaded. Any hooks/hijacks/monkeying about that
    the script did should be reverted here"""

    add_callback(callback_map['callbacks_script_unloaded'], callback)


def on_before_ui(callback):
    """register a function to be called before the UI is created."""
    add_callback(callback_map['callbacks_before_ui'], callback)
