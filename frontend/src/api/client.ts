import type { Order, Driver, Merchant, Shift } from '../types'

const API_BASE = '/api'

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(error.error || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Orders
  getOrders: (merchantId: number, page = 1, perPage = 50) =>
    request<{
      orders: Order[]
      total: number
      page: number
      per_page: number
      total_pages: number
    }>(`/orders?merchant_id=${merchantId}&page=${page}&per_page=${perPage}`),

  createOrder: (data: {
    merchant_id: number
    description?: string
    pickup_time: string
    dropoff_time: string
    weight: number
  }) => request<Order>('/orders', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  updateOrder: (orderId: number, data: {
    merchant_id: number
    description?: string
    pickup_time?: string
    dropoff_time?: string
    weight?: number
  }) => request<Order>(`/orders/${orderId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  cancelOrder: (orderId: number) =>
    request<{ message: string }>(`/orders/${orderId}`, {
      method: 'DELETE',
    }),

  // Drivers
  getDrivers: () => request<Driver[]>('/drivers'),

  // Merchants
  getMerchants: () => request<Merchant[]>('/merchants'),

  // Shifts
  getShifts: () => request<Shift[]>('/shifts'),

  // CSV Upload
  uploadCSV: (file: File, type: 'merchants' | 'drivers' | 'vehicles' | 'orders') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)

    return fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    }).then(res => {
      if (!res.ok) {
        return res.json().then(err => { throw new Error(err.error || 'Upload failed') })
      }
      return res.json()
    })
  },
}

