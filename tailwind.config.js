/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './frontend/templates/**/*.html',
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#F08C21",
                "on-primary": "#ffffff",
                "primary-container": "#FFF3E5",
                "on-primary-container": "#854500",
                "secondary": "#6698CC",
                "on-secondary": "#ffffff",
                "secondary-container": "#E6F0FA",
                "on-secondary-container": "#1B3B5C",
                "tertiary": "#E36888",
                "on-tertiary": "#ffffff",
                "tertiary-container": "#FDECEF",
                "on-tertiary-container": "#7A1C33",
                "background": "#FFFDF9",
                "surface": "#ffffff",
                "on-surface": "#1C1C18",
                "on-surface-variant": "#414751",
                "outline": "#727782",
                "outline-variant": "#E0E0E0",
                "error": "#ba1a1a",
                // Antigravity palette
                "tangerine": "#F08C21",
                "butter": "#F2D88F",
                "blush": "#E36888",
                "sea": "#6698CC",
                "matcha": "#B4B534",
                "matcha-dark": "#7C7D20",
            },
            borderRadius: {
                DEFAULT: "0.25rem",
                lg: "0.5rem",
                xl: "0.75rem",
                full: "9999px"
            },
            spacing: {
                "base": "8px",
                "stack-md": "24px",
                "gutter": "24px",
                "stack-sm": "12px",
                "stack-lg": "48px",
                "margin-mobile": "20px",
                "margin-desktop": "64px"
            },
            fontFamily: {
                "display-lg": ["Plus Jakarta Sans"],
                "label-md": ["Plus Jakarta Sans"],
                "headline-md": ["Plus Jakarta Sans"],
                "headline-lg": ["Plus Jakarta Sans"],
                "body-lg": ["Quicksand"],
                "headline-lg-mobile": ["Plus Jakarta Sans"],
                "body-md": ["Quicksand"]
            },
            fontSize: {
                "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "800" }],
                "label-md": ["14px", { lineHeight: "20px", fontWeight: "700" }],
                "headline-md": ["24px", { lineHeight: "32px", fontWeight: "600" }],
                "headline-lg": ["32px", { lineHeight: "40px", fontWeight: "700" }],
                "body-lg": ["18px", { lineHeight: "28px", fontWeight: "500" }],
                "headline-lg-mobile": ["28px", { lineHeight: "36px", fontWeight: "700" }],
                "body-md": ["16px", { lineHeight: "24px", fontWeight: "500" }]
            }
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
