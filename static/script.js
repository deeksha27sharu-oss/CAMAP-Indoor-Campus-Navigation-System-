// Map rendering functionality
class MapRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isDragging = false;
        this.lastX = 0;
        this.lastY = 0;
        
        // Store graph data and path
        this.graphData = null;
        this.currentPath = null;
        this.startNodeKey = null;
        this.endNodeKey = null;
        this.currentFloor = 'ground'; // Default floor
        
        // Initialize event listeners
        this.initializeEventListeners();
        
        // Calculate optimal initial view to fit all nodes
        this.calculateOptimalView();
    }

    calculateOptimalView() {
        if (!this.graphData) {
            // Default view if no graph data
            this.scale = 0.8;
            this.offsetX = -this.canvas.width / 2 + 600;
            this.offsetY = -this.canvas.height / 2 + 400;
            return;
        }

        const { nodes } = this.graphData;
        
        // Find the bounding box of all nodes
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        for (const node of Object.values(nodes)) {
            if (node.x < minX) minX = node.x;
            if (node.y < minY) minY = node.y;
            if (node.x > maxX) maxX = node.x;
            if (node.y > maxY) maxY = node.y;
        }
        
        // Add some padding around the nodes
        const padding = 100;
        minX -= padding;
        minY -= padding;
        maxX += padding;
        maxY += padding;
        
        // Calculate the center of the map
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        
        // Calculate the required scale to fit the map in the canvas
        const mapWidth = maxX - minX;
        const mapHeight = maxY - minY;
        
        const scaleX = this.canvas.width / mapWidth;
        const scaleY = this.canvas.height / mapHeight;
        
        // Use the smaller scale to ensure everything fits
        this.scale = Math.min(scaleX, scaleY, 1) * 0.9; // 0.9 for a little extra padding
        
        // Calculate offset to center the map
        this.offsetX = -centerX * this.scale + this.canvas.width / 2;
        this.offsetY = -centerY * this.scale + this.canvas.height / 2;
    }

    initializeEventListeners() {
        // Mouse wheel for zooming
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const zoomIntensity = 0.1;
            const wheel = e.deltaY < 0 ? 1 : -1;
            const zoom = Math.exp(wheel * zoomIntensity);
            
            const mouseX = e.offsetX / this.scale - this.offsetX / this.scale;
            const mouseY = e.offsetY / this.scale - this.offsetY / this.scale;
            
            this.scale *= zoom;
            this.offsetX = (this.offsetX - mouseX * (zoom - 1)) * zoom;
            this.offsetY = (this.offsetY - mouseY * (zoom - 1)) * zoom;
            
            this.draw();
        });

        // Mouse events for panning
        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.lastX = e.clientX;
            this.lastY = e.clientY;
            this.canvas.style.cursor = 'grabbing';
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const dx = e.clientX - this.lastX;
                const dy = e.clientY - this.lastY;
                
                this.offsetX += dx;
                this.offsetY += dy;
                
                this.lastX = e.clientX;
                this.lastY = e.clientY;
                
                this.draw();
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
        });

        this.canvas.addEventListener('mouseleave', () => {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
        });

        // Set initial cursor
        this.canvas.style.cursor = 'grab';
    }

    setGraphData(graphData) {
        this.graphData = graphData;
        this.calculateOptimalView();
        this.draw();
    }

    setCurrentFloor(floor) {
        this.currentFloor = floor;
        this.draw();
    }

    updatePath(path, startNodeKey, endNodeKey) {
        this.currentPath = path;
        this.startNodeKey = startNodeKey;
        this.endNodeKey = endNodeKey;
        this.draw();
    }

    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Save context
        this.ctx.save();
        
        // Apply transformations
        this.ctx.scale(this.scale, this.scale);
        this.ctx.translate(this.offsetX, this.offsetY);
        
        // Draw map background
        this.drawMapBackground();
        
        // Draw map elements
        this.drawMapElements();
        
        // Draw path if available
        if (this.currentPath) {
            this.drawPath();
        }
        
        // Restore context
        this.ctx.restore();
    }

    drawMapBackground() {
        // Draw a subtle grid or background to help with orientation
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(-10000, -10000, 20000, 20000);
        
        // Draw a subtle grid
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        this.ctx.lineWidth = 1;
        const gridSize = 100;
        
        for (let x = -1000; x <= 2000; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, -1000);
            this.ctx.lineTo(x, 2000);
            this.ctx.stroke();
        }
        
        for (let y = -1000; y <= 2000; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(-1000, y);
            this.ctx.lineTo(2000, y);
            this.ctx.stroke();
        }
    }

    drawMapElements() {
        if (!this.graphData) return;

        const { nodes, adjacency } = this.graphData;

        // Draw edges (connections between nodes) - only for current floor
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.lineWidth = 2;
        
        for (const [nodeId, connections] of Object.entries(adjacency)) {
            const nodeA = nodes[nodeId];
            if (!nodeA || nodeA.floor !== this.currentFloor) continue;
            
            for (const [connectedNodeId] of Object.entries(connections)) {
                const nodeB = nodes[connectedNodeId];
                if (!nodeB || nodeB.floor !== this.currentFloor) continue;
                
                this.ctx.beginPath();
                this.ctx.moveTo(nodeA.x, nodeA.y);
                this.ctx.lineTo(nodeB.x, nodeB.y);
                this.ctx.stroke();
            }
        }

        // Draw nodes - only for current floor
        for (const [nodeId, node] of Object.entries(nodes)) {
            if (node.floor === this.currentFloor) {
                this.drawNode(node, nodeId);
            }
        }
    }

    // Updated drawNode function in script.js
drawNode(node, nodeId) {
    const { x, y, type, label } = node;
    
    // Determine node color based on type
    let color = '#ffffff';
    let radius = 6;
    
    switch (type) {
        case 'classroom':
            color = '#4ecf92';
            break;
        case 'lab':
            color = '#29b6f6';
            break;
        case 'office':
            color = '#ffa726';
            break;
        case 'Department':
            color = '#9c27b0';
            radius = 8;
            break;
        case 'stairs':
            color = '#795548';
            radius = 5;
            break;
        case 'Washroom':
            color = '#607d8b';
            break;
        case 'Canteen':
            color = '#f44336';
            break;
        case 'Entrance':
            color = '#00bcd4';
            radius = 8;
            break;
        case 'Garden':
            color = '#388e3c';
            break;
        case 'Room':
            color = '#757575';
            break;
        case 'seminar':
            color = '#7b1fa2';
            break;
        case 'common':
            color = '#f57c00';
            break;
        case 'connector':
            color = '#455a64';
            radius = 4;
            break;
        case 'lift':
            color = '#ffeb3b'; // Yellow color for lift
            radius = 7;
            break;
        default:
            color = '#cccccc';
    }

    // Highlight start and end nodes
    if (nodeId === this.startNodeKey) {
        color = '#28a745';
        radius = 12;
    } else if (nodeId === this.endNodeKey) {
        color = '#dc3545';
        radius = 12;
    }

    // Draw node circle
    this.ctx.fillStyle = color;
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
    this.ctx.fill();

    // Draw node outline
    this.ctx.strokeStyle = '#ffffff';
    this.ctx.lineWidth = 1;
    this.ctx.stroke();

    // Draw node label (only for important nodes or when zoomed in)
    if (this.scale > 0.5 || type === 'Department' || type === 'Entrance' || type === 'lift' || 
        nodeId === this.startNodeKey || nodeId === this.endNodeKey) {
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        this.ctx.fillText(label, x, y + radius + 2);
    }
}

    drawPath() {
        if (!this.currentPath || !this.graphData) return;

        const { nodes } = this.graphData;

        // Draw the path line - only for current floor segments
        this.ctx.strokeStyle = '#007bff';
        this.ctx.lineWidth = 4;
        this.ctx.lineJoin = 'round';
        this.ctx.lineCap = 'round';

        this.ctx.beginPath();
        
        let lastValidPoint = null;
        
        for (let i = 0; i < this.currentPath.length; i++) {
            const nodeId = this.currentPath[i];
            const node = nodes[nodeId];
            if (!node) continue;
            
            // Only draw segments where both nodes are on current floor
            if (node.floor === this.currentFloor) {
                if (lastValidPoint === null) {
                    this.ctx.moveTo(node.x, node.y);
                } else {
                    this.ctx.lineTo(node.x, node.y);
                }
                lastValidPoint = { x: node.x, y: node.y };
            } else {
                lastValidPoint = null;
            }
        }
        
        this.ctx.stroke();

        // Draw path nodes with highlights - only for current floor
        for (let i = 0; i < this.currentPath.length; i++) {
            const nodeId = this.currentPath[i];
            const node = nodes[nodeId];
            if (!node || node.floor !== this.currentFloor) continue;

            // Skip drawing start/end nodes again as they're already highlighted
            if (nodeId !== this.startNodeKey && nodeId !== this.endNodeKey) {
                this.ctx.fillStyle = '#007bff';
                this.ctx.beginPath();
                this.ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
                this.ctx.fill();
                
                this.ctx.strokeStyle = '#ffffff';
                this.ctx.lineWidth = 1;
                this.ctx.stroke();
            }
        }
    }

    // Helper methods for map controls
    zoomIn() {
        this.scale *= 1.2;
        this.draw();
    }

    zoomOut() {
        this.scale /= 1.2;
        this.draw();
    }

    resetView() {
        this.calculateOptimalView();
        this.draw();
    }
}

// Initialize map controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // These will be set up in route.html
    const zoomInBtn = document.getElementById('zoomIn');
    const zoomOutBtn = document.getElementById('zoomOut');
    const resetViewBtn = document.getElementById('resetView');

    if (zoomInBtn && window.mapRenderer) {
        zoomInBtn.addEventListener('click', () => window.mapRenderer.zoomIn());
    }
    if (zoomOutBtn && window.mapRenderer) {
        zoomOutBtn.addEventListener('click', () => window.mapRenderer.zoomOut());
    }
    if (resetViewBtn && window.mapRenderer) {
        resetViewBtn.addEventListener('click', () => window.mapRenderer.resetView());
    }
});