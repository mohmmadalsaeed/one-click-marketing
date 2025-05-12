"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { format, parseISO, isValid } from 'date-fns';

interface MessageTemplate {
  id: number;
  template_name: string;
  category: string;
  language_code: string;
  template_structure_json: string;
  variables_expected_json: string | null;
  status: string;
  meta_rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

interface ViewTemplateDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  template: MessageTemplate | null;
}

function formatDateSafe(dateString?: string): string {
  if (!dateString) return 'N/A';
  try {
    const parsedDate = parseISO(dateString);
    if (!isValid(parsedDate)) {
        return 'Invalid Date';
    }
    return format(parsedDate, "MMM d, yyyy HH:mm");
  } catch (error) {
    return 'Date Error';
  }
}

function formatStatusSafe(statusString?: string): string {
    if (!statusString || typeof statusString !== 'string') return 'N/A';
    return statusString.replace(/_/g, " ");
}

export default function ViewTemplateDialog({ isOpen, onOpenChange, template }: ViewTemplateDialogProps) {
  if (!template) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>View Template: {template.template_name}</DialogTitle>
          <DialogDescription>
            Category: {template.category} | Language: {template.language_code} | Status: {formatStatusSafe(template.status)}
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-3">
          <div>
            <h4 className="font-semibold text-sm mb-1">Template Structure:</h4>
            <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-md text-xs overflow-x-auto">
              {JSON.stringify(JSON.parse(template.template_structure_json), null, 2)}
            </pre>
          </div>
          {template.variables_expected_json && template.variables_expected_json !== "[]" && (
            <div>
              <h4 className="font-semibold text-sm mb-1">Variables Expected:</h4>
              <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-md text-xs overflow-x-auto">
                {JSON.stringify(JSON.parse(template.variables_expected_json), null, 2)}
              </pre>
            </div>
          )}
          {template.status === "REJECTED_BY_META" && template.meta_rejection_reason && (
            <div>
              <h4 className="font-semibold text-sm mb-1">Meta Rejection Reason:</h4>
              <p className="text-sm text-red-600 dark:text-red-400">{template.meta_rejection_reason}</p>
            </div>
          )}
          <div>
            <h4 className="font-semibold text-sm mb-1">Created At:</h4>
            <p className="text-sm">{formatDateSafe(template.created_at)}</p>
          </div>
          <div>
            <h4 className="font-semibold text-sm mb-1">Last Updated:</h4>
            <p className="text-sm">{formatDateSafe(template.updated_at)}</p>
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild><Button variant="outline">Close</Button></DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

