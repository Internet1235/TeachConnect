title = TeachConnect

package.name = com.teachconnect

package.domain = org.teachconnect

source.dir = .

source.include_exts = py,png,jpg,kv,atlas,ttf,mp3

source.main = main.py

version = 1.0

version.code = 1

android.api = 33

android.minapi = 21

android.targetapi = 33

# android.sdk_path =

# android.ndk_path =

requirements = python3,kivy,kivymd,openssl,requests,pyjnius

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.features = android.hardware.wifi

icon.filename = /img/TC-T.ico

# presplash.filename = presplash.png

android.arch = armeabi-v7a,arm64-v8a

entrypoint = main.py

log_level = 2

[buildozer]

log_level = 2