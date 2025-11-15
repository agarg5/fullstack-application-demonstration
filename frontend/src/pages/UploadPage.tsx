import { useState } from 'react'
import { api } from '../api/client'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { Upload, CheckCircle, XCircle } from 'lucide-react'

const CSV_TYPES = [
  { value: 'merchants', label: 'Merchants' },
  { value: 'drivers', label: 'Drivers' },
  { value: 'vehicles', label: 'Vehicles' },
  { value: 'orders', label: 'Orders' },
] as const

export default function UploadPage() {
  const [selectedType, setSelectedType] = useState<string>('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<{
    success: boolean
    message: string
  } | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
    }
  }

  const handleUpload = async () => {
    if (!file || !selectedType) {
      setResult({
        success: false,
        message: 'Please select a file type and file',
      })
      return
    }

    setUploading(true)
    setResult(null)

    try {
      await api.uploadCSV(
        file,
        selectedType as 'merchants' | 'drivers' | 'vehicles' | 'orders'
      )
      setResult({
        success: true,
        message: `Successfully uploaded ${selectedType} CSV file`,
      })
      setFile(null)
      setSelectedType('')
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement
      if (fileInput) fileInput.value = ''
    } catch (error) {
      setResult({
        success: false,
        message:
          error instanceof Error
            ? error.message
            : 'Failed to upload CSV file',
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">CSV Import</h1>

      <div className="rounded-md border p-6">
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Data Type</label>
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger>
                <SelectValue placeholder="Select data type" />
              </SelectTrigger>
              <SelectContent>
                {CSV_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">CSV File</label>
            <Input
              id="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
            />
            {file && (
              <p className="text-sm text-muted-foreground">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          <Button
            onClick={handleUpload}
            disabled={!file || !selectedType || uploading}
            className="w-full"
          >
            {uploading ? (
              'Uploading...'
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload CSV
              </>
            )}
          </Button>

          {result && (
            <div
              className={`flex items-center gap-2 rounded-md p-4 ${
                result.success
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {result.success ? (
                <CheckCircle className="h-5 w-5" />
              ) : (
                <XCircle className="h-5 w-5" />
              )}
              <span>{result.message}</span>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-md border p-6">
        <h2 className="mb-4 text-lg font-semibold">CSV Format Requirements</h2>
        <div className="space-y-4 text-sm">
          <div>
            <h3 className="font-semibold">Merchants</h3>
            <p className="text-muted-foreground">
              Columns: id, name, email
            </p>
          </div>
          <div>
            <h3 className="font-semibold">Drivers</h3>
            <p className="text-muted-foreground">
              Columns: id, name
            </p>
          </div>
          <div>
            <h3 className="font-semibold">Vehicles</h3>
            <p className="text-muted-foreground">
              Columns: id, driver_id, max_orders, max_weight
            </p>
          </div>
          <div>
            <h3 className="font-semibold">Orders</h3>
            <p className="text-muted-foreground">
              Columns: id, merchant_id, driver_id, vehicle_id, status,
              description, pickup_time, dropoff_time, weight
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

