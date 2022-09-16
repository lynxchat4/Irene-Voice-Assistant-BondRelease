import { z } from 'zod';

export const Message = z.object({
    type: z.string(),
});

export const NegotiationAgreeMessage = Message.extend({
    type: z.enum(['negotiate/agree']),
    protocols: z.array(z.string().or(z.null())),
});

export const TextOutputMessage = Message.extend({
    type: z.enum(['out.text-plain/text']),
    text: z.string(),
});

export const PlaybackRequestMessage = z.object({
    type: z.enum(['out.audio.link/playback-request']),
    url: z.string(),
    playbackId: z.string(),
    altText: z.string().optional(),
});
