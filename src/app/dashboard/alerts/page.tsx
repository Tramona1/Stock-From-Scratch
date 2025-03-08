"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Bell, Plus, X } from "lucide-react"

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([
    { id: 1, symbol: "AAPL", condition: "Price above", value: "$185.00", triggered: false },
    { id: 2, symbol: "MSFT", condition: "RSI below", value: "30", triggered: true },
    { id: 3, symbol: "NVDA", condition: "Volume spike", value: "2x average", triggered: false },
  ])
  
  const removeAlert = (id: number) => {
    setAlerts(alerts.filter(alert => alert.id !== id))
  }
  
  return (
    <div className="container p-6 space-y-6">
      <h1 className="text-3xl font-bold">Alerts</h1>
      
      <div className="flex justify-between items-center">
        <p className="text-muted-foreground">Get notified when market conditions match your criteria.</p>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Alert
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Your Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {alerts.map(alert => (
              <div key={alert.id} className="border rounded-lg p-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <Bell className={`h-5 w-5 ${alert.triggered ? 'text-red-500' : 'text-muted-foreground'}`} />
                  <div>
                    <h3 className="font-medium">{alert.symbol}: {alert.condition} {alert.value}</h3>
                    <p className="text-sm text-muted-foreground">Created May 15, 2023</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {alert.triggered && 
                    <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Triggered</Badge>
                  }
                  <Button variant="ghost" size="icon" onClick={() => removeAlert(alert.id)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 