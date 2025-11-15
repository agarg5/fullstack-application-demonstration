import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import OrdersPage from '../OrdersPage'
import { api } from '../../api/client'

// Mock the API client
vi.mock('../../api/client', () => ({
  api: {
    getOrders: vi.fn(),
    getMerchants: vi.fn(),
    createOrder: vi.fn(),
    updateOrder: vi.fn(),
    cancelOrder: vi.fn(),
  },
}))

describe('OrdersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the orders page', async () => {
    vi.mocked(api.getMerchants).mockResolvedValue([
      { id: 1, name: 'Test Merchant', email: 'test@example.com' }
    ])
    vi.mocked(api.getOrders).mockResolvedValue([])

    render(<OrdersPage />)

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument()
    })
  })

  it('loads and displays orders', async () => {
    const mockOrders = [
      {
        order_id: 1,
        merchant_id: 1,
        status: 'pending',
        description: 'Test Order',
        pickup_time: '2025-01-20T10:00:00',
        dropoff_time: '2025-01-20T12:00:00',
        weight: 50.5,
        driver_id: null,
      },
    ]

    vi.mocked(api.getMerchants).mockResolvedValue([
      { id: 1, name: 'Test Merchant', email: 'test@example.com' }
    ])
    vi.mocked(api.getOrders).mockResolvedValue(mockOrders)

    render(<OrdersPage />)

    await waitFor(() => {
      expect(screen.getByText('Test Order')).toBeInTheDocument()
      expect(screen.getByText('pending')).toBeInTheDocument()
    })
  })

  it('opens create order dialog', async () => {
    const user = userEvent.setup()
    vi.mocked(api.getMerchants).mockResolvedValue([
      { id: 1, name: 'Test Merchant', email: 'test@example.com' }
    ])
    vi.mocked(api.getOrders).mockResolvedValue([])

    render(<OrdersPage />)

    await waitFor(() => {
      expect(screen.getByText('Create Order')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: /create order/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('Create Order')).toBeInTheDocument()
      expect(screen.getByText(/fill in the details/i)).toBeInTheDocument()
    })
  })
})

