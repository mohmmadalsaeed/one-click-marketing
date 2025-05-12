// frontend/src/app/dashboard/meta-integration/page.tsx
"use client";

import { useState, useEffect, FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast"; // Assuming you have a toast component

interface MetaCredentialsStatus {
  credentials_set: boolean;
  phone_number_id: string | null;
  waba_id: string | null;
}

export default function MetaIntegrationPage() {
  const [accessToken, setAccessToken] = useState("");
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [wabaId, setWabaId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<MetaCredentialsStatus | null>(null);
  const { toast } = useToast();

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("authToken"); // Assuming token is stored in localStorage
      if (!token) {
        toast({
          title: "Authentication Error",
          description: "No auth token found. Please log in again.",
          variant: "destructive",
        });
        return;
      }
      const response = await fetch("/api/v1/meta/credentials", {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data: MetaCredentialsStatus = await response.json();
        setStatus(data);
        if (data.credentials_set) {
          setPhoneNumberId(data.phone_number_id || "");
          setWabaId(data.waba_id || "");
          // Do not pre-fill access token for security
        }
      } else {
        const errorData = await response.json();
        toast({
          title: "Error fetching status",
          description: errorData.message || "Could not retrieve Meta integration status.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Network Error",
        description: "Failed to connect to the server to fetch status.",
        variant: "destructive",
      });
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);

    const token = localStorage.getItem("authToken");
    if (!token) {
      toast({
        title: "Authentication Error",
        description: "No auth token found. Please log in again.",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/v1/meta/credentials", {
        method: "POST", // Or PUT, depending on your backend logic for create/update
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          access_token: accessToken, 
          phone_number_id: phoneNumberId, 
          waba_id: wabaId 
        }),
      });

      const responseData = await response.json();
      if (response.ok) {
        toast({
          title: "Success",
          description: "Meta API credentials saved successfully.",
        });
        setAccessToken(""); // Clear sensitive field after submission
        fetchStatus(); // Refresh status
      } else {
        toast({
          title: "Error Saving Credentials",
          description: responseData.message || "An unknown error occurred.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Network Error",
        description: "Failed to connect to the server.",
        variant: "destructive",
      });
    }
    setIsLoading(false);
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <h1 className="text-2xl font-bold mb-6">WhatsApp Business API Integration</h1>

      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-3">Connection Status</h2>
        {isLoading && !status && <p>Loading status...</p>}
        {status && (
          <div className={`p-3 rounded-md ${status.credentials_set ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {status.credentials_set ? (
              <p>
                Successfully connected to WhatsApp Business API.
                <br />
                Phone Number ID: <strong>{status.phone_number_id}</strong>
                <br />
                WABA ID: <strong>{status.waba_id}</strong>
              </p>
            ) : (
              <p>Not connected. Please provide your API credentials below.</p>
            )}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6 space-y-6">
        <h2 className="text-xl font-semibold mb-4">Configure Credentials</h2>
        
        <div>
          <Label htmlFor="wabaId">WhatsApp Business Account ID (WABA ID)</Label>
          <Input 
            id="wabaId" 
            type="text" 
            value={wabaId} 
            onChange={(e) => setWabaId(e.target.value)} 
            placeholder="Enter your WABA ID"
            required 
          />
        </div>

        <div>
          <Label htmlFor="phoneNumberId">Phone Number ID</Label>
          <Input 
            id="phoneNumberId" 
            type="text" 
            value={phoneNumberId} 
            onChange={(e) => setPhoneNumberId(e.target.value)} 
            placeholder="Enter your Phone Number ID"
            required 
          />
        </div>

        <div>
          <Label htmlFor="accessToken">Permanent System User Access Token</Label>
          <Input 
            id="accessToken" 
            type="password" // Use password type for sensitive fields
            value={accessToken} 
            onChange={(e) => setAccessToken(e.target.value)} 
            placeholder="Enter your Access Token (will not be displayed again)"
            required 
          />
          <p className="text-sm text-gray-500 mt-1">This token is sensitive and will be stored securely. It will not be shown again after saving.</p>
        </div>

        <Button type="submit" disabled={isLoading} className="w-full md:w-auto">
          {isLoading ? "Saving..." : "Save Credentials"}
        </Button>
      </form>
      
      <div className="mt-8 p-4 bg-blue-50 border-l-4 border-blue-500 text-blue-700">
        <h3 className="font-semibold">Important Notes:</h3>
        <ul className="list-disc list-inside mt-2 text-sm">
          <li>Ensure the credentials you provide are correct and have the necessary permissions.</li>
          <li>The Access Token should be a **Permanent System User Access Token**.</li>
          <li>If you need help obtaining these credentials, please refer to the WhatsApp Onboarding Guide provided earlier or Meta's official documentation.</li>
        </ul>
      </div>
    </div>
  );
}

