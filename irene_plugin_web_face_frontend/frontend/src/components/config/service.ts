import { z } from 'zod';
import axios from 'axios';

export const Config = z.object({
    scope: z.string(),
    config: z.any(),
    comment: z.string().optional(),
});

export type Config = z.infer<typeof Config>;

const ConfigList = z.array(Config);

export const fetchConfigs = async () => {
    const res = await axios.get('/api/config/configs');

    return ConfigList.parse(res.data);
}

export const fetchConfig = async (scope: string) => {
    const res = await axios.get(`/api/config/${scope}`);

    return Config.parse(res.data);
}

export const updateConfig = async (scope: string, config: object) => {
    await axios.patch(`/api/config/configs/${scope}`, config);
}
