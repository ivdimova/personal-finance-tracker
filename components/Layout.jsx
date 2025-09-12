import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, CreditCard, Receipt, Settings } from 'lucide-react'

const Layout = ({ children }) => {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/transactions', label: 'Transactions', icon: CreditCard },
    { path: '/receipts', label: 'Receipts', icon: Receipt },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  const isActive = (path) => {
    return location.pathname === path
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-500 to-indigo-600">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6">
            <h1 className="text-3xl font-bold text-center">
              💰 Personal Finance Tracker
            </h1>
            <p className="text-center text-purple-100 mt-2">
              Track expenses, manage receipts, and take control of your finances
            </p>
          </div>

          {/* Navigation */}
          <nav className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="flex justify-center space-x-1">
              {navItems.map(({ path, label, icon: Icon }) => (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                    isActive(path)
                      ? 'bg-purple-100 text-purple-700 font-semibold'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon size={20} />
                  <span className="hidden md:inline">{label}</span>
                </Link>
              ))}
            </div>
          </nav>

          {/* Main Content */}
          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}

export default Layout