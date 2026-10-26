# LocalAI models

LocalAI reads one model definition per YAML file from `/models`. The model
binaries and voice files are stored in the `localai_models` Docker volume.

## TTS voice

The Piper voice `ca_ES-upc_ona-medium` is downloaded from the
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) repository:

- `ca/ca_ES/upc_ona/medium/ca_ES-upc_ona-medium.onnx`
  (MD5 `58ff3b049b6b721a4c353a551ec5ef3a`)
- `ca/ca_ES/upc_ona/medium/ca_ES-upc_ona-medium.onnx.json`
  (MD5 `035e9eb642ab9fa1354f53a77877ae9b`)

Place both files in the volume root:

```sh
docker run --rm -v librechat_localai_models:/models alpine \
  sh -c 'cd /models && wget -q \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/ca/ca_ES/upc_ona/medium/ca_ES-upc_ona-medium.onnx \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/ca/ca_ES/upc_ona/medium/ca_ES-upc_ona-medium.onnx.json'
```
