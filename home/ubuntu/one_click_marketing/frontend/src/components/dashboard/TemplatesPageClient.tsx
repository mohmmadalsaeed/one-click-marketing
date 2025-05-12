"use client";

import { useState, useEffect, FormEvent, useCallback } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
// import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { PlusCircle, Edit, Trash2, Eye } from "lucide-react";
import { format, parseISO, isValid } from 'date-fns';

// Commented out useToast for SSR compatibility
// import { useToast } from "@/hooks/use-toast";

const AddEditTemplateDialog = dynamic(() => import("@/components/dashboard/AddEditTemplateDialog"), { ssr: false });
const ViewTemplateDialog = dynamic(() => import("@/components/dashboard/ViewTemplateDialog"), { ssr: false });

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

const initialTemplateFormState = {
  id: 0,
  template_name: "",
  category: "UTILITY",
  language_code: "en_US",
  template_structure_json: JSON.stringify({
    header: { type: "TEXT", text: "Your Header {{1}}" },
    body: { text: "Hello {{2}}, your appointment is on {{3}}." },
    footer: { text: "Thank you!" },
    buttons: [{ type: "QUICK_REPLY", text: "Confirm" }]
  }, null, 2),
  variables_expected_json: "[]",
  status: "DRAFT",
  meta_rejection_reason: null,
};

function formatDateSafe(dateString?: string): string {
  if (!dateString) return 'N/A';
  try {
    const parsedDate = parseISO(dateString);
    if (!isValid(parsedDate)) {
        return 'Invalid Date';
    }
    return format(parsedDate, "MMM d, yyyy HH:mm");
  } catch (error) {
    console.error("Error formatting date:", error);
    return 'Date Error';
  }
}

function formatStatusSafe(statusString?: string): string {
    if (!statusString || typeof statusString !== 'string') return 'N/A';
    return statusString.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
}

export default function TemplatesPageClient() {
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<MessageTemplate | null>(null);
  const [formData, setFormData] = useState<Omit<MessageTemplate, "id" | "created_at" | "updated_at"> & { id?: number }>(initialTemplateFormState);
  
  // Replaced useToast with a simple console.log function for SSR compatibility
  const toast = (args: any) => {
    console.log("Toast notification:", args);
  };

  const fetchTemplates = useCallback(async () => {
    if (typeof window === "undefined") return;
    setIsLoading(true);
    try {
      const token = localStorage.getItem("authToken");
      if (!token) {
        console.log("Authentication Error: Please log in again.");
        setIsLoading(false);
        return;
      }
      const response = await fetch("/api/v1/templates", {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (response.ok) {
        const data: MessageTemplate[] = await response.json();
        setTemplates(data);
      } else {
        const errorData = await response.json();
        console.log("Error fetching templates:", errorData.message || "Could not retrieve templates.");
      }
    } catch (error) {
      console.log("Network Error: Failed to connect to the server.");
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (typeof window === "undefined") return;
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) {
      console.log("Authentication Error");
      setIsLoading(false);
      return;
    }

    const method = formData.id ? "PUT" : "POST";
    const url = formData.id ? `/api/v1/templates/${formData.id}` : "/api/v1/templates";

    try {
      JSON.parse(formData.template_structure_json);
      if (formData.variables_expected_json) JSON.parse(formData.variables_expected_json);
    } catch (e) {
      console.log("Invalid JSON: Template Structure or Variables Expected is not valid JSON.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(formData),
      });
      const responseData = await response.json();
      if (response.ok) {
        console.log(formData.id ? "Template Updated" : "Template Created", responseData.message);
        fetchTemplates();
        setIsDialogOpen(false);
      } else {
        console.log("Error:", responseData.message || "An unknown error occurred.");
      }
    } catch (error) {
      console.log("Network Error");
    }
    setIsLoading(false);
  };

  const handleEdit = (template: MessageTemplate) => {
    setFormData({
      id: template.id,
      template_name: template.template_name,
      category: template.category,
      language_code: template.language_code,
      template_structure_json: template.template_structure_json,
      variables_expected_json: template.variables_expected_json || "[]",
      status: template.status,
      meta_rejection_reason: template.meta_rejection_reason,
    });
    setIsDialogOpen(true);
  };

  const handleView = (template: MessageTemplate) => {
    setCurrentTemplate(template);
    setIsViewDialogOpen(true);
  };

  const handleDelete = async (templateId: number) => {
    if (typeof window === "undefined") return;
    if (!confirm("Are you sure you want to delete this template?")) return; // Consider a custom confirm dialog
    setIsLoading(true);
    const token = localStorage.getItem("authToken");
    if (!token) {
      console.log("Authentication Error");
      setIsLoading(false);
      return;
    }
    try {
      const response = await fetch(`/api/v1/templates/${templateId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` },
      });
      const responseData = await response.json();
      if (response.ok) {
        console.log("Template Deleted:", responseData.message);
        fetchTemplates();
      } else {
        console.log("Error Deleting Template:", responseData.message);
      }
    } catch (error) {
      console.log("Network Error");
    }
    setIsLoading(false);
  };

  const openNewTemplateDialog = () => {
    setFormData(initialTemplateFormState);
    setIsDialogOpen(true);
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Message Templates</h1>
        <Button onClick={openNewTemplateDialog}>Add New Template</Button>
      </div>

      {/* Replaced Card with div for debugging */}
      <div>
        {/* Replaced CardHeader with div for debugging */}
        <div>
          {/* Replaced CardTitle with div for debugging */}
          <div>Your Templates</div>
          {/* Replaced CardDescription with div for debugging */}
          <div>Manage your WhatsApp message templates here. Ensure templates are approved by Meta before use in active campaigns.</div>
        </div>
        {/* Replaced CardContent with div for debugging */}
        <div>
          {isLoading && templates.length === 0 ? (
            <p>Loading templates...</p>
          ) : templates.length === 0 ? (
            <p>No templates found. Click "Add New Template" to create one.</p>
          ) : (
            <p>Table component and its usage are commented out for debugging SSR issues.</p>
          )}
        </div>
      </div>
      {/* Add/Edit Template Dialog */}
      {isDialogOpen && (
        <AddEditTemplateDialog
          isOpen={isDialogOpen}
          onOpenChange={setIsDialogOpen}
          formData={formData}
          handleInputChange={handleInputChange}
          handleSelectChange={handleSelectChange}
          handleFormSubmit={handleFormSubmit}
          isLoading={isLoading}
        />
      )}

      {currentTemplate && (
        <ViewTemplateDialog
            isOpen={isViewDialogOpen}
            onOpenChange={setIsViewDialogOpen}
            template={currentTemplate}
        />
      )}
    </div>
  );
}
