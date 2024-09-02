
# Тестовое задание: Внедрение функции "Audio Inputs" от SUNO в боте

Проект: Разработка новой функции в боте GPT-Expert (

Цель: Реализовать функцию аудиовхода, позволяющую пользователям записывать или загружать аудио для дальнейшей генерации аудио на основе загруженного файла.

 Описание задачи:
   - Пользователи должны иметь возможность записывать аудио напрямую в боте или загружать существующие аудио.
   - Поддержка клипов длиной от 6 до 60 секунд.
   - Возможность расширения загруженных клипов путем добавления новых фрагментов.

# Реализация API
## Архитектура решения 

Для реализации выбран следующий стек технологий   

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)  
![pythonversion](https://img.shields.io/badge/python-%3E%3D3.11.9-blue)  

## Краткое описание реализация

Для загрузки файлов добавлен хендлер /uploads. Который принимает URL аудио файла.
Функциональность хендлера:
1. Быстрое скачивание файлов
2. Быструю загрузку файла 
3. Проверка формата файла
   - проверка длительности аудио
   - проверка расширения
   - конвертацию voice сообщений ogg формата телеграмм в wav формат.
   - Настройка дефолтных значений конвертации
5. Добавлена обработка ошибок
6. Логгирование

Хендлер реализует процесс загрущки фалов в суно который состоит из этапов:
1. Получение данных для загружаемого файла (url, key, policy ...)
2. Скачивание файла частями с сервиса телеграмм и отправку его в облачное хранилище Суно.
Скачивание происходит без загрузки в файловую систему, сразу в память сервера. Конвертация и анализ трека происходит также в памяти. Тем самым увеличиваем производительность. Потребление по памятя должно быть незначительным, так при **48000HZ, 16.bit, 2stereo, 60s** не компрессированный файл занимает **~12МЬ**.
3. 
#### Калькулятор размера аудиофайла:
    https://toolstud.io/video/audiosize.php ?samplerate=48000&sampledepth=16&channelcount=2&timeduration=60&timeunit=seconds

**Можно улучшить:** Получать и сразу передавать поток чанками, при этом анализировать небольшую часть загаловка аудиофала, который передается в первом чанке, для oпределения его типа. Тоесть можно зафильтровать файл сразу с первым куском данных. Aiohttp плохо поддерживает multipart stream. Лучше использовать httpx.

5. Анализ аулио на длительность. При необходимости происходи конвертация, так как ogg не поддерживатся Suno.

4. Сообщаем суно что файл загружен.
5. Делаем ретрай статуса загрузки в системе Суно. Модерация проходит следующие этапы:
`starus:["processing", "passed_artist_moderation", "complete", "error", ""passed_audio_processing]`
Здесь на каждый статус можно предусмотреть исключение и переиспользовать в боте, для большей информативности что происходит с загрузкой файла и в какой она стадии. Добавил просто общее исключение.
6. Финализируем загрузку в Суно и получаем `clip_id`. Его и возвращаем repons с id.

Для анализа аудио фала и конвертации сделал отдельный класс `StreamLister`. Который можно будет расширить. В принципе тут можно еще зарефакторить. Сделать отдельный класс загрузчика и добавить немного архитектуры :). Так я постарался не ломать код, дописать в стиле который есть.

Релизация кода в пул реквесте. в репо https://github.com/26remph/Vtoraya_Suno-API/tree/upload-add-on

# Реализация Telegram-Bot

Здесь особо описывать нечего. Добавил требуемый функционал на основе предоставленного кода. Максимально старался ниччего не ломать.

Процесс выглядит так.  

![tg-bot.png](data%2Ftg-bot.png)

Релизация кода в пул реквесте в репо https://github.com/RadaShapp/Test_Test
.

### Требования к запуску

Необходимо, чтобы были установлены следующие компоненты:

- `Docker` и `docker-compose`
- `Python 3.11.9`



<details><summary> Техническая информация для разработки </summary>
<p>


# Suno API add-on

## Upload

POST https://studio-api.suno.ai/api/uploads/audio/

### Headers
Authorization: Bearer
"Key-id"

### payload
```json
{
  "extension": "mp3"
}
```

### response

Content-Encoding: br

```json
{
    "id": "03ee986b-64f5-4450-b35e-b4a188eb7d40",
    "url": "https://suno-uploads.s3.amazonaws.com/",
    "fields": {
        "Content-Type": "audio/mpeg",
        "key": "raw_uploads/03ee986b-64f5-4450-b35e-b4a188eb7d40.mp3",
        "AWSAccessKeyId": "AKIA2V4GXGDKJMTPWLXO",
        "policy": "eyJleHBpcmF0aW9uIjogIjIwMjQtMDgtMjBUMTc6MDU6MzhaIiwgImNvbmRpdGlvbnMiOiBbWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsIDAsIDEwNDg1NzYwMF0sIFsic3RhcnRzLXdpdGgiLCAiJENvbnRlbnQtVHlwZSIsICJhdWRpby9tcGVnIl0sIHsiYnVja2V0IjogInN1bm8tdXBsb2FkcyJ9LCB7ImtleSI6ICJyYXdfdXBsb2Fkcy8wM2VlOTg2Yi02NGY1LTQ0NTAtYjM1ZS1iNGExODhlYjdkNDAubXAzIn1dfQ==",
        "signature": "7fEUl0iKObc9sByYN41GkziYERo="
    },
    "is_file_uploaded": false
}
```

---
## S3 upload
POST https://suno-uploads.s3.amazonaws.com/
### Headers
`
POST / HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: ru,en;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 169475
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary5qvgBUgD9SnzhqKg
Host: suno-uploads.s3.amazonaws.com
Origin: https://suno.com
Pragma: no-cache
Referer: https://suno.com/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: cross-site
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36
sec-ch-ua: "Not/A)Brand";v="8", "Chromium";v="126", "YaBrowser";v="24.7", "Yowser";v="2.5"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "macOS"
`
### Payload
`Content-Type: audio/mpeg
key: raw_uploads/03ee986b-64f5-4450-b35e-b4a188eb7d40.mp3
AWSAccessKeyId: AKIA2V4GXGDKJMTPWLXO
policy: eyJleHBpcmF0aW9uIjogIjIwMjQtMDgtMjBUMTc6MDU6MzhaIiwgImNvbmRpdGlvbnMiOiBbWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsIDAsIDEwNDg1NzYwMF0sIFsic3RhcnRzLXdpdGgiLCAiJENvbnRlbnQtVHlwZSIsICJhdWRpby9tcGVnIl0sIHsiYnVja2V0IjogInN1bm8tdXBsb2FkcyJ9LCB7ImtleSI6ICJyYXdfdXBsb2Fkcy8wM2VlOTg2Yi02NGY1LTQ0NTAtYjM1ZS1iNGExODhlYjdkNDAubXAzIn1dfQ==
signature: 7fEUl0iKObc9sByYN41GkziYERo=
file: (binary)`

---
## Upload finish

POST https://studio-api.suno.ai/api/uploads/audio/03ee986b-64f5-4450-b35e-b4a188eb7d40/upload-finish/
### payload
```json
{
  "upload_type": "file_upload",
  "upload_filename": "sample-test2.mp3"
}
```

---
## GET status
GET https://studio-api.suno.ai/api/uploads/audio/03ee986b-64f5-4450-b35e-b4a188eb7d40/

[//]: # (starus:["processing", "passed_artist_moderation", "complete", "error", ""passed_audio_processing])
### response
```json
{
    "id": "03ee986b-64f5-4450-b35e-b4a188eb7d40",
    "status": "complete",
    "error_message": null,
    "s3_id": "m_14e88b8f-8d0b-4b2b-a9ea-c822c9572b41",
    "title": "sample-track3",
    "image_url": "https://cdn2.suno.ai/image_14e88b8f-8d0b-4b2b-a9ea-c822c9572b41.jpeg"
}
```
## Initialize clip

POST https://studio-api.suno.ai/api/uploads/audio/03ee986b-64f5-4450-b35e-b4a188eb7d40/initialize-clip/

### response
```json
{"clip_id": "14e88b8f-8d0b-4b2b-a9ea-c822c9572b41"}
```

---

## FEED presets
[//]: # (track_id: f8af2469-78a2-4588-a69c-0c13c08b2196)
GET https://studio-api.suno.ai/api/feed/v2?page=0
response = {...} 


## Generate
POST https://studio-api.suno.ai/api/gen/f8af2469-78a2-4588-a69c-0c13c08b2196/increment_play_count/v2
```json
{
  "sample_factor": 1
}
```

POST https://studio-api.suno.ai/api/generate/v2/
### payload
```json
{
  "prompt": "That Arizona sky\nBurnin' in your eyes\nYou look at me and babe I wanna catch on fire\nIt’s buried in my soul\nLike California gold\nYou found the light in me that I couldn’t find",
  "generation_type": "TEXT",
  "tags": "soul country",
  "negative_tags": "",
  "mv": "chirp-v3-5-upload",
  "title": "Always Remember",
  "continue_clip_id": "f8af2469-78a2-4588-a69c-0c13c08b2196",
  "continue_at": 25.200000000000003,
  "infill_start_s": null,
  "infill_end_s": null
}
```

### response
```json
{
    "id": "cffc3660-0409-4378-865f-16d9ae36efad",
    "clips": [
        {
            "id": "9ed699f0-a2fe-43e5-bd9d-5b0c00ff525d",
            "video_url": "",
            "audio_url": "",
            "image_url": null,
            "image_large_url": null,
            "is_video_pending": false,
            "major_model_version": "v3",
            "model_name": "chirp-v3",
            "metadata": {
                "tags": "soul country",
                "negative_tags": "",
                "prompt": "That Arizona sky\nBurnin' in your eyes\nYou look at me and babe I wanna catch on fire\nIt\u2019s buried in my soul\nLike California gold\nYou found the light in me that I couldn\u2019t find",
                "gpt_description_prompt": null,
                "audio_prompt_id": "m_f8af2469-78a2-4588-a69c-0c13c08b2196",
                "history": [
                    {
                        "id": "m_f8af2469-78a2-4588-a69c-0c13c08b2196",
                        "continue_at": 25.200000000000003,
                        "type": "upload",
                        "source": "web",
                        "infill": false
                    }
                ],
                "concat_history": null,
                "stem_from_id": null,
                "type": "gen",
                "duration": null,
                "refund_credits": null,
                "stream": true,
                "infill": false,
                "has_vocal": false,
                "is_audio_upload_tos_accepted": true,
                "error_type": null,
                "error_message": null,
                "configurations": null,
                "artist_clip_id": null,
                "cover_clip_id": null
            },
            "is_liked": false,
            "user_id": "39572d22-15e6-4182-9078-35600c847b17",
            "display_name": "SpectralFrequencies814",
            "handle": "spectralfrequencies814",
            "is_handle_updated": false,
            "avatar_image_url": "https://cdn1.suno.ai/defaultPink.webp",
            "is_trashed": false,
            "reaction": null,
            "created_at": "2024-08-20T14:46:42.482Z",
            "status": "submitted",
            "title": "Always Remember",
            "play_count": 0,
            "upvote_count": 0,
            "is_public": false
        },
        {
            "id": "11caca94-8c67-4608-9c0d-330afacffa6d",
            "video_url": "",
            "audio_url": "",
            "image_url": null,
            "image_large_url": null,
            "is_video_pending": false,
            "major_model_version": "v3",
            "model_name": "chirp-v3",
            "metadata": {
                "tags": "soul country",
                "negative_tags": "",
                "prompt": "That Arizona sky\nBurnin' in your eyes\nYou look at me and babe I wanna catch on fire\nIt\u2019s buried in my soul\nLike California gold\nYou found the light in me that I couldn\u2019t find",
                "gpt_description_prompt": null,
                "audio_prompt_id": "m_f8af2469-78a2-4588-a69c-0c13c08b2196",
                "history": [
                    {
                        "id": "m_f8af2469-78a2-4588-a69c-0c13c08b2196",
                        "continue_at": 25.200000000000003,
                        "type": "upload",
                        "source": "web",
                        "infill": false
                    }
                ],
                "concat_history": null,
                "stem_from_id": null,
                "type": "gen",
                "duration": null,
                "refund_credits": null,
                "stream": true,
                "infill": false,
                "has_vocal": false,
                "is_audio_upload_tos_accepted": true,
                "error_type": null,
                "error_message": null,
                "configurations": null,
                "artist_clip_id": null,
                "cover_clip_id": null
            },
            "is_liked": false,
            "user_id": "39572d22-15e6-4182-9078-35600c847b17",
            "display_name": "SpectralFrequencies814",
            "handle": "spectralfrequencies814",
            "is_handle_updated": false,
            "avatar_image_url": "https://cdn1.suno.ai/defaultPink.webp",
            "is_trashed": false,
            "reaction": null,
            "created_at": "2024-08-20T14:46:42.482Z",
            "status": "submitted",
            "title": "Always Remember",
            "play_count": 0,
            "upvote_count": 0,
            "is_public": false
        }
    ],
    "metadata": {
        "tags": "soul country",
        "negative_tags": "",
        "prompt": "That Arizona sky\nBurnin' in your eyes\nYou look at me and babe I wanna catch on fire\nIt\u2019s buried in my soul\nLike California gold\nYou found the light in me that I couldn\u2019t find",
        "gpt_description_prompt": null,
        "audio_prompt_id": "m_f8af2469-78a2-4588-a69c-0c13c08b2196",
        "history": [
            {
                "id": "m_f8af2469-78a2-4588-a69c-0c13c08b2196",
                "continue_at": 25.200000000000003,
                "type": "upload",
                "source": "web",
                "infill": false
            }
        ],
        "concat_history": null,
        "stem_from_id": null,
        "type": "gen",
        "duration": null,
        "refund_credits": null,
        "stream": true,
        "infill": false,
        "has_vocal": false,
        "is_audio_upload_tos_accepted": true,
        "error_type": null,
        "error_message": null,
        "configurations": null,
        "artist_clip_id": null,
        "cover_clip_id": null
    },
    "major_model_version": "v3",
    "status": "complete",
    "created_at": "2024-08-20T14:46:42.472Z",
    "batch_size": 1
}
```
</p>
</details>