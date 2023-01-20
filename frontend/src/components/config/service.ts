import { z } from 'zod';
import axios from 'axios';

export const Config = z.object({
    scope: z.string(),
    config: z.any(),
    comment: z.string().optional(),
});

// scope конфигурации, отвечающий за настройки браузерного интерфейса
export const FRONTEND_CONFIG_SCOPE = 'web_face_frontend';

export type Config = z.infer<typeof Config>;

const ConfigList = z.array(Config);

export const fetchConfigs = async () => {
    const res = await axios.get('/api/config/configs');

    return ConfigList.parse(res.data);
}

export const fetchConfig = async (scope: string) => {
    const res = await axios.get(`/api/config/configs/${scope}`);

    return Config.parse(res.data);
}

export const updateConfig = async (scope: string, config: object) => {
    await axios.patch(`/api/config/configs/${scope}`, config);

    if (scope === FRONTEND_CONFIG_SCOPE && (config as any).autoReload) {
        // перезагружаем страницу если настройки браузерного интерфейса были изменены и автоматическая перезагрузка включена в новых настройках
        window.location.reload();
    }
}
