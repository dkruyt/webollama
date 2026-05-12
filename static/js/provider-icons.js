/**
 * Provider icon helpers — shared across pages that use the custom model dropdown.
 * Exposes: getProviderIcon(modelName), resolveIconSrc(modelName)
 */

function getProviderIcon(modelName) {
    const raw = (modelName || '').toLowerCase();
    // For hf.co/<user>/<model> — match against the model-name segment first, fall back to HuggingFace
    const isHf = raw.startsWith('hf.co/');
    const name = isHf ? raw.split('/').slice(2).join('/') : raw;
    const map = [
        [/deepseek/,                                        'deepseek-color.svg'],
        [/llama|meta/,                                      'meta-color.svg'],
        [/gemma/,                                           'gemma-color.svg'],
        [/gemini/,                                          'gemini-color.svg'],
        [/mistral|mixtral|codestral|devstral|ministral/,    'mistral-color.svg'],
        [/phi/,                                             'microsoft-color.svg'],
        [/copilot/,                                         'copilot-color.svg'],
        [/qwen/,                                            'qwen-color.svg'],
        [/grok/,                                            'grok.svg'],
        [/groq/,                                            'groq.svg'],
        [/claude|anthropic/,                                'claude-color.svg'],
        [/gpt|openai/,                                      'openai.svg'],
        [/command|cohere/,                                  'cohere-color.svg'],
        [/perplexity|pplx|sonar/,                           'perplexity.svg'],
        [/stable.?diffusion|sdxl|stability|stablelm/,       'stability-color.svg'],
        [/minimax|abab/,                                    'minimax-color.svg'],
        [/doubao|skylark|bytedance/,                        'bytedance-color.svg'],
        [/\byi\b|yi[-_]|01-ai|zeroone/,                     'zeroone-color.svg'],
        [/chatglm|glm|zhipu/,                               'zai.svg'],
        [/fireworks/,                                       'fireworks-color.svg'],
        [/kling/,                                           'kling-color.svg'],
        [/luma/,                                            'luma-color.svg'],
        [/midjourney/,                                      'midjourney.svg'],
        [/replicate/,                                       'replicate.svg'],
        [/kimi/,                                            'kimi.png'],
        [/snowflake/,                                       'snowflake-color.svg'],
        [/nomic/,                                           'nomic.png'],
        [/ibm|granite/,                                     'granite.svg'],
        [/jan|jan-nano|lucy/,                               'menlo-color.svg'],
        [/starcoder|falcon/,                                'huggingface-color.svg'],
    ];
    for (const [pattern, icon] of map) {
        if (pattern.test(name)) return icon;
    }
    return isHf ? 'huggingface-color.svg' : null;
}

function resolveIconSrc(modelName) {
    const icon = getProviderIcon(modelName);
    if (!icon) return null;
    const mode = document.documentElement.classList.contains('dark') ? 'dark-mode' : 'light-mode';
    return `/assets/icons/${mode}/${icon}`;
}
