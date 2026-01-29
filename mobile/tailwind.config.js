/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./App.{js,jsx,ts,tsx}", "./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            colors: {
                primary: "#1A2F5A", // Darker blue matching reference header
                "primary-dark": "#0F1E3B",
                secondary: "#E2E8F0", // Added missing secondary color
                accent: "#FF4500", // Adjusted to match the orange/red bar reference
                "accent-light": "#FFF5F5",
                "accent-btn": "#EF4444", // Bright red for active filter
                "background-light": "#E2E8F0", // Darker slate for better contrast with white cards
                "background-dark": "#111827",
                "card-light": "#FFFFFF",
                "card-dark": "#1F2937",
                "text-main-light": "#1E293B",
                "text-main-dark": "#F3F4F6",
                "text-sub-light": "#64748B",
                "text-sub-dark": "#9CA3AF",
                "status-green": "#22C55E",
                "chat-orange": "#FF6B2C", // Vibrant orange for chat button
                "brand-navy": "#1e3a5f", // Custom navy based on reference
                "brand-orange": "#f97316", // Orange accent for brand
                "brand-red": "#FF4500", // Vibrant red/orange for the button
            },
            fontFamily: {
                sans: ["Inter", "sans-serif"],
            },
        },
    },
    plugins: [],
}
