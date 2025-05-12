"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { FormEvent } from "react";

// This interface would ideally be imported from a shared types file
interface FormDataShape {
  id?: number;
  template_name: string;
  category: string;
  language_code: string;
  template_structure_json: string;
  variables_expected_json: string | null;
  status: string;
  meta_rejection_reason?: string | null;
}

interface AddEditTemplateDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  formData: FormDataShape;
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  handleSelectChange: (name: string, value: string) => void;
  handleFormSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  isLoading: boolean;
}

export default function AddEditTemplateDialog({
  isOpen,
  onOpenChange,
  formData,
  handleInputChange,
  handleSelectChange,
  handleFormSubmit,
  isLoading,
}: AddEditTemplateDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{formData.id ? "Edit" : "Add New"} Message Template</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleFormSubmit} className="space-y-4 py-4">
            <div>
              <Label htmlFor="template_name">Template Name (as in Meta)</Label>
              <Input id="template_name" name="template_name" value={formData.template_name} onChange={handleInputChange} required />
              <p className="text-xs text-gray-500 mt-1">Must match the name approved by Meta.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <Label htmlFor="category">Category</Label>
                    <Select name="category" value={formData.category} onValueChange={(value) => handleSelectChange("category", value)}>
                        <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                        <SelectContent>
                        <SelectItem value="MARKETING">Marketing</SelectItem>
                        <SelectItem value="UTILITY">Utility</SelectItem>
                        <SelectItem value="AUTHENTICATION">Authentication</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div>
                    <Label htmlFor="language_code">Language Code</Label>
                    <Input id="language_code" name="language_code" value={formData.language_code} onChange={handleInputChange} placeholder="e.g., en_US, ar" required />
                </div>
            </div>
            <div>
              <Label htmlFor="template_structure_json">Template Structure (JSON)</Label>
              <Textarea id="template_structure_json" name="template_structure_json" value={formData.template_structure_json} onChange={handleInputChange}rows={6} placeholder={
              JSON.stringify({
                header: { type: "TEXT", text: "Your Header {{1}}" },
                body: { text: "Hello {{2}}, your appointment is on {{3}}." },
                footer: { text: "Thank you!" },
                buttons: [{ type: "QUICK_REPLY", text: "Confirm" }]
              }, null, 2)
              } />
              <p className="text-xs text-gray-500 mt-1">Define the header, body, footer, and buttons as per Meta specifications. Use {{n}} for variables.</p>
            </div>
            <div>
              <Label htmlFor="variables_expected_json">Variables Expected (JSON Array)</Label>
              <Input id="variables_expected_json" name="variables_expected_json" value={formData.variables_expected_json || ""} onChange={handleInputChange} placeholder={'[]'} />
              <p className="text-xs text-gray-500 mt-1">Optional. List variable names if you want to map them. E.g., ["customer_name", "order_id"].</p>
            </div>
            <div>
                <Label htmlFor="status">Status</Label>
                <Select name="status" value={formData.status} onValueChange={(value) => handleSelectChange("status", value)}>
                    <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="DRAFT">Draft</SelectItem>
                        <SelectItem value="PENDING_META_APPROVAL">Pending Meta Approval</SelectItem>
                        <SelectItem value="APPROVED_BY_META">Approved by Meta</SelectItem>
                        <SelectItem value="REJECTED_BY_META">Rejected by Meta</SelectItem>
                        <SelectItem value="PAUSED">Paused</SelectItem>
                        <SelectItem value="DISABLED">Disabled</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            {formData.status === "REJECTED_BY_META" && (
                <div>
                    <Label htmlFor="meta_rejection_reason">Meta Rejection Reason</Label>
                    <Textarea id="meta_rejection_reason" name="meta_rejection_reason" value={formData.meta_rejection_reason || ""} onChange={handleInputChange} />
                </div>
            )}
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">Cancel</Button>
            </DialogClose>
            <Button type="submit" disabled={isLoading}>{isLoading ? "Saving..." : "Save Template"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

