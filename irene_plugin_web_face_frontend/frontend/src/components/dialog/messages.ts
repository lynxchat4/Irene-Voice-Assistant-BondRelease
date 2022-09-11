import { z } from 'zod';

export const Message = z.object({
    type: z.string(),
});

export const NegotiationAgreeMessage = Message.extend({
    type: z.enum(['negotiate/agree']),
    protocols: z.array(z.string()),
});

export const TextOutputMessage = Message.extend({
    type: z.enum(['out.text-plain/text']),
    text: z.string(),
});
