import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import UploadPage from '../UploadPage'
import { api } from '../../api/client'

// Mock the API client
vi.mock('../../api/client', () => ({
  api: {
    uploadCSV: vi.fn(),
  },
}))

describe('UploadPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the upload form', () => {
    render(<UploadPage />)

    expect(screen.getByText('CSV Import')).toBeInTheDocument()
    expect(screen.getByLabelText(/data type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/csv file/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /upload csv/i })).toBeInTheDocument()
  })

  it('disables upload button when no file or type selected', () => {
    render(<UploadPage />)

    const uploadButton = screen.getByRole('button', { name: /upload csv/i })
    expect(uploadButton).toBeDisabled()
  })

  it('shows error when trying to upload without file and type', async () => {
    const user = userEvent.setup()
    render(<UploadPage />)

    const uploadButton = screen.getByRole('button', { name: /upload csv/i })
    await user.click(uploadButton)

    await waitFor(() => {
      expect(screen.getByText(/please select a file type and file/i)).toBeInTheDocument()
    })
  })

  it('handles successful CSV upload', async () => {
    const user = userEvent.setup()
    vi.mocked(api.uploadCSV).mockResolvedValue({ message: 'Success', count: 5 })

    render(<UploadPage />)

    // Select type - click on the select trigger
    const typeSelect = screen.getByPlaceholderText(/select data type/i)
    await user.click(typeSelect)

    // Wait for and click Merchants option
    const merchantsOption = await screen.findByText('Merchants')
    await user.click(merchantsOption)

    // Create a mock file
    const file = new File(['id,name,email\n1,Test,test@test.com'], 'test.csv', {
      type: 'text/csv',
    })

    const fileInput = screen.getByLabelText(/csv file/i) as HTMLInputElement
    await user.upload(fileInput, file)

    // Upload
    const uploadButton = screen.getByRole('button', { name: /upload csv/i })
    await user.click(uploadButton)

    await waitFor(() => {
      expect(api.uploadCSV).toHaveBeenCalledWith(file, 'merchants')
      expect(screen.getByText(/successfully uploaded merchants csv file/i)).toBeInTheDocument()
    })
  })

  it('handles upload error', async () => {
    const user = userEvent.setup()
    vi.mocked(api.uploadCSV).mockRejectedValue(new Error('Upload failed'))

    render(<UploadPage />)

    // Select type
    const typeSelect = screen.getByPlaceholderText(/select data type/i)
    await user.click(typeSelect)

    const driversOption = await screen.findByText('Drivers')
    await user.click(driversOption)

    // Create a mock file
    const file = new File(['id,name\n1,Test'], 'test.csv', {
      type: 'text/csv',
    })

    const fileInput = screen.getByLabelText(/csv file/i) as HTMLInputElement
    await user.upload(fileInput, file)

    // Upload
    const uploadButton = screen.getByRole('button', { name: /upload csv/i })
    await user.click(uploadButton)

    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument()
    })
  })

  it('shows file name and size when file is selected', async () => {
    const user = userEvent.setup()
    render(<UploadPage />)

    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const fileInput = screen.getByLabelText(/csv file/i) as HTMLInputElement

    await user.upload(fileInput, file)

    expect(screen.getByText(/selected: test\.csv/i)).toBeInTheDocument()
  })

  it('displays CSV format requirements', () => {
    render(<UploadPage />)

    expect(screen.getByText('CSV Format Requirements')).toBeInTheDocument()
    expect(screen.getByText(/merchants/i)).toBeInTheDocument()
    expect(screen.getByText(/drivers/i)).toBeInTheDocument()
    expect(screen.getByText(/vehicles/i)).toBeInTheDocument()
    expect(screen.getByText(/orders/i)).toBeInTheDocument()
  })
})

