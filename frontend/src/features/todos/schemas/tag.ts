import { z } from "zod";

export const tagSchema = z.object({
  name: z.string().trim().min(1, "Tag name is required").max(50, "Tag name is too long"),
  color: z.string().max(20, "Color is too long").optional(),
});

export type TagFormData = z.infer<typeof tagSchema>;