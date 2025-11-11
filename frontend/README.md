# SEO SaaS Tool - Frontend

Modern React frontend for SEO SaaS Tool built with Vite, TypeScript, and Tailwind CSS.

## Features

- 📊 **Dashboard** - Overview of projects, usage stats, and recent activity
- 📁 **Project Management** - Create, view, and manage SEO projects
- 🕷️ **Crawl Management** - Start and monitor crawls (Fast/JavaScript modes)
- 📈 **Usage Analytics** - Track API usage, quotas, and trends
- 🎨 **Modern UI** - Clean, responsive design with Tailwind CSS
- 🔒 **Secure** - API key authentication stored locally
- ⚡ **Fast** - Vite for lightning-fast development and builds

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable React components
│   │   └── Layout.tsx    # Main layout with sidebar
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx    # Dashboard overview
│   │   ├── Projects.tsx     # Projects list
│   │   ├── ProjectDetail.tsx # Project details & crawls
│   │   ├── Usage.tsx        # Usage & quotas
│   │   └── Login.tsx        # Login with API key
│   ├── lib/             # Utilities and helpers
│   │   └── api.ts       # API client
│   ├── types/           # TypeScript types
│   │   └── index.ts     # Type definitions
│   ├── App.tsx          # Main App component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── package.json         # Dependencies
```

## API Integration

The frontend communicates with the backend API using the `APIClient` class in `src/lib/api.ts`.

### Authentication

API keys are stored in localStorage and included in all requests:

```typescript
import { api } from '@/lib/api';

// Set API key (done in Login component)
api.setApiKey('sk_test_...');

// Make authenticated requests
const projects = await api.getProjects();
```

### Available API Methods

```typescript
// Projects
api.getProjects()
api.getProject(id)
api.createProject(data)
api.updateProject(id, data)
api.deleteProject(id)

// Crawls
api.startCrawl({ project_id, mode, config })
api.getCrawlJob(id)
api.getProjectCrawls(projectId)

// Pages
api.getPages(projectId, params)
api.getPage(id)

// Usage & Quotas
api.getQuota()
api.getUsageStats(year, month)
api.getUsageHistory(months)

// Content Generation
api.generateMetaDescription(payload)
api.generateTitleSuggestions(payload)
api.generateRecommendations(payload)

// Analysis
api.generateEmbeddings(projectId)
api.computeGraph(projectId)
api.getRecommendations(projectId, topK)
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### Proxy Configuration

The dev server proxies `/api` requests to the backend (configured in `vite.config.ts`):

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

## Development

### Code Style

```bash
# Lint code
npm run lint

# Format code
npm run format
```

### TypeScript

Type checking is done automatically during build. All API responses are typed in `src/types/index.ts`.

### Tailwind CSS

Custom styles are defined in `tailwind.config.js` and `src/index.css`. Use utility classes in components:

```tsx
<div className="card">  {/* Custom component class */}
  <button className="btn btn-primary">  {/* Custom button classes */}
    Click me
  </button>
</div>
```

## Features Overview

### Dashboard
- Overview statistics (projects, API calls, pages crawled)
- Recent projects list
- Quick actions
- Quota warnings

### Projects
- Create new projects
- View all projects as cards
- Delete projects
- Quick access to project details

### Project Details
- Project information
- Start crawl modal (Fast/JS mode)
- Recent crawls with status
- Pages table with pagination
- Real-time status updates

### Usage & Quotas
- Current plan information
- API usage progress bar
- Monthly usage stats
- Usage trend chart (last 6 months)
- Remaining quotas

## Deployment

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Static Hosting

Build and deploy the `dist` folder to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

## Troubleshooting

### API Connection Issues

If you see connection errors:
1. Check backend is running on http://localhost:8000
2. Verify CORS is enabled in backend
3. Check API key is valid

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite
```

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new files
3. Add types for API responses
4. Test on different screen sizes
5. Update this README for new features

## License

Part of SEO SaaS Tool project.
