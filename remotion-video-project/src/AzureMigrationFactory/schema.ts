import { z } from "zod";

/**
 * Every video/audio field is optional. Leave it unset to render the
 * stylized navy/azure placeholder for that act instead of real footage —
 * useful for previz while the AI-generated clips aren't ready yet.
 */
export const azureMigrationFactorySchema = z.object({
  showDirectorNotes: z.boolean().default(true),
  act1VideoUrl: z.string().nullable().default(null),
  act2VideoUrl: z.string().nullable().default(null),
  act3VideoUrl: z.string().nullable().default(null),
  act4VideoUrl: z.string().nullable().default(null),
  act5VideoUrl: z.string().nullable().default(null),
  voAudioUrl: z.string().nullable().default(null),
  musicUrl: z.string().nullable().default(null),
});

export type AzureMigrationFactorySchemaType = z.infer<typeof azureMigrationFactorySchema>;
