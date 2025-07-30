import { render, screen } from '@testing-library/react'
import Home from './page'

describe('Home Page', () => {
  it('renders the main heading', () => {
    render(<Home />)
    
    const heading = screen.getByRole('heading', { 
      name: /rpm - solar performance monitoring/i 
    })
    
    expect(heading).toBeInTheDocument()
  })

  it('renders the view site portfolio button', () => {
    render(<Home />)
    
    const button = screen.getByRole('button', { name: /view site portfolio/i })
    
    expect(button).toBeInTheDocument()
  })

  it('renders the site overview section', () => {
    render(<Home />)
    
    const siteOverview = screen.getByText(/site overview/i)
    
    expect(siteOverview).toBeInTheDocument()
  })
})