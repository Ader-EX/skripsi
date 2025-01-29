/** @type {import('tailwindcss').Config} */
const { fontFamily } = require("tailwindcss/defaultTheme");
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			primary: {
  				DEFAULT: '#3B82F6',
  				foreground: '#FFFFFF'
  			},
  			secondary: {
  				DEFAULT: '#F97316',
  				foreground: '#FFFFFF'
  			},
  			background: '#FFFFFF',
  			surface: '#F9FAFB',
  			border: '#E5E7EB',
  			text: {
  				primary: '#1F2937',
  				secondary: '#6B7280',
  				disabled: '#9CA3AF'
  			},
  			success: '#10B981',
  			error: '#EF4444',
  			warning: '#F59E0B',
  			info: '#3B82F6',
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))'
  			}
  		},
  		fontFamily: {
  			sans: [
  				'Inter',
                    ...fontFamily.sans
                ],
  			mono: [
  				'JetBrains Mono',
                    ...fontFamily.mono
                ]
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};
