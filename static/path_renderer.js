// Path-based map rendering functionality with floor segmentation and GPS support
class PathRenderer {
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
        this.pathData = null;
        this.currentFloorPaths = {
            'ground': null,
            'first': null,
            'second': null,
            'third': null
        };
        this.startNodeKey = null;
        this.endNodeKey = null;
        this.currentFloor = 'ground';
        this.gpsMarker = null; // Store GPS marker
        
        // Initialize event listeners
        this.initializeEventListeners();
        
        // Load path data
        this.loadPathData();
    }

    async loadPathData() {
        try {
            const response = await fetch('/get-path-data');
            this.pathData = await response.json();
            this.calculateOptimalView();
            this.draw();
        } catch (error) {
            console.error('Error loading path data:', error);
        }
    }

    calculateOptimalView() {
        if (!this.pathData) {
            // Default view if no path data
            this.scale = 0.8;
            this.offsetX = -this.canvas.width / 2 + 600;
            this.offsetY = -this.canvas.height / 2 + 400;
            return;
        }

        // Find the bounding box of all paths
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        Object.values(this.pathData).forEach(floorPaths => {
            floorPaths.forEach(path => {
                path.points.forEach(point => {
                    const [x, y] = point;
                    if (x < minX) minX = x;
                    if (y < minY) minY = y;
                    if (x > maxX) maxX = x;
                    if (y > maxY) maxY = y;
                });
            });
        });

        // Add some padding around the paths
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
        this.scale = Math.min(scaleX, scaleY, 1) * 0.9;
        
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

    updatePath(floorSegmentedPaths, startNodeKey, endNodeKey) {
        this.currentFloorPaths = floorSegmentedPaths;
        this.startNodeKey = startNodeKey;
        this.endNodeKey = endNodeKey;
        this.draw();
    }

    setGPSMarker(gpsNode) {
        this.gpsMarker = gpsNode;
        this.draw();
    }

    clearGPSMarker() {
        this.gpsMarker = null;
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
        
        // Draw corridors and paths for current floor only
        this.drawCorridors();
        
        // Draw current route path for current floor only
        this.drawCurrentPath();
        
        // Draw rooms and landmarks for current floor only
        this.drawLandmarks();
        
        // Draw GPS marker if available and on current floor
        this.drawGPSMarker();
        
        // Restore context
        this.ctx.restore();
    }

    drawMapBackground() {
        // Draw a dark background
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

    drawCorridors() {
        if (!this.pathData || !this.pathData[this.currentFloor]) return;

        const floorPaths = this.pathData[this.currentFloor];
        
        floorPaths.forEach(path => {
            // Draw corridor path
            this.ctx.strokeStyle = '#4a5568';
            this.ctx.lineWidth = 12;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            
            this.ctx.beginPath();
            path.points.forEach((point, index) => {
                const [x, y] = point;
                if (index === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            });
            this.ctx.stroke();
            
            // Draw corridor outline
            this.ctx.strokeStyle = '#2d3748';
            this.ctx.lineWidth = 14;
            this.ctx.stroke();
        });
    }

    drawCurrentPath() {
        // Only draw the path for the current floor
        const currentFloorPath = this.currentFloorPaths[this.currentFloor];
        if (!currentFloorPath || currentFloorPath.length < 2) return;

        // Draw the main path line for current floor
        this.ctx.strokeStyle = '#007bff';
        this.ctx.lineWidth = 8;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        this.ctx.beginPath();
        currentFloorPath.forEach((point, index) => {
            const [x, y] = point;
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        this.ctx.stroke();
        
        // Draw path outline for better visibility
        this.ctx.strokeStyle = '#0056b3';
        this.ctx.lineWidth = 10;
        this.ctx.stroke();
        
        // Draw start and end markers only if they are on current floor
        if (this.graphData && this.startNodeKey && this.endNodeKey) {
            const startNode = this.graphData.nodes[this.startNodeKey];
            const endNode = this.graphData.nodes[this.endNodeKey];
            
            if (startNode && startNode.floor === this.currentFloor) {
                this.drawMarker([startNode.x, startNode.y], 'start');
            }
            if (endNode && endNode.floor === this.currentFloor) {
                this.drawMarker([endNode.x, endNode.y], 'end');
            }
        }
    }

    drawMarker(point, type) {
        const [x, y] = point;
        const radius = 15;
        const color = type === 'start' ? '#28a745' : '#dc3545';
        
        // Outer circle
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // Inner circle
        this.ctx.fillStyle = '#ffffff';
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius - 5, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // Icon
        this.ctx.fillStyle = color;
        if (type === 'start') {
            // Draw circle for start
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius - 8, 0, 2 * Math.PI);
            this.ctx.fill();
        } else {
            // Draw X for end
            this.ctx.font = 'bold 16px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('×', x, y);
        }
    }

    drawGPSMarker() {
        if (!this.gpsMarker || this.gpsMarker.floor !== this.currentFloor) return;

        const { x, y } = this.gpsMarker;
        const radius = 12;
        
        // Draw pulsing effect
        const time = Date.now() / 1000;
        const pulse = (Math.sin(time * 3) + 1) / 2;
        const pulseRadius = radius + pulse * 5;
        
        // Outer pulsing circle
        this.ctx.fillStyle = `rgba(255, 215, 0, ${0.3 + pulse * 0.2})`;
        this.ctx.beginPath();
        this.ctx.arc(x, y, pulseRadius, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // Main GPS marker
        this.ctx.fillStyle = '#ffd700'; // Gold color for GPS
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // Inner dot
        this.ctx.fillStyle = '#ffffff';
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius - 4, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // GPS icon
        this.ctx.fillStyle = '#ff6b00';
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius - 7, 0, 2 * Math.PI);
        this.ctx.fill();
        
        // Label
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        this.ctx.fillText('GPS', x, y + radius + 2);
    }

    drawLandmarks() {
        if (!this.graphData) return;

        const { nodes } = this.graphData;
        
        // Draw rooms and landmarks for current floor only
        Object.entries(nodes).forEach(([nodeId, node]) => {
            if (node.floor === this.currentFloor) {
                this.drawRoom(node, nodeId);
            }
        });
    }

    drawRoom(node, nodeId) {
        const { x, y, type, label } = node;
        
        // Determine room color based on type
        let color = '#718096';
        let radius = 6;
        
        switch (type) {
            case 'classroom':
                color = '#4ecf92';
                radius = 8;
                break;
            case 'lab':
                color = '#29b6f6';
                radius = 8;
                break;
            case 'office':
                color = '#ffa726';
                radius = 7;
                break;
            case 'Department':
                color = '#9c27b0';
                radius = 10;
                break;
            case 'stairs':
                color = '#795548';
                radius = 6;
                break;
            case 'Washroom':
                color = '#607d8b';
                radius = 6;
                break;
            case 'Canteen':
                color = '#f44336';
                radius = 9;
                break;
            case 'Entrance':
                color = '#00bcd4';
                radius = 10;
                break;
            case 'Garden':
                color = '#388e3c';
                radius = 8;
                break;
            case 'Room':
                color = '#757575';
                radius = 6;
                break;
            case 'seminar':
                color = '#7b1fa2';
                radius = 9;
                break;
            case 'common':
                color = '#f57c00';
                radius = 7;
                break;
            case 'connector':
                color = '#455a64';
                radius = 4;
                break;
            case 'lift':
                color = '#ffeb3b';
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

        // Draw room circle
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fill();

        // Draw room outline
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();

        // Draw room label (only when zoomed in or for important rooms)
        if (this.scale > 0.5 || type === 'Department' || type === 'Entrance' || 
            nodeId === this.startNodeKey || nodeId === this.endNodeKey) {
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '10px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'top';
            this.ctx.fillText(label, x, y + radius + 2);
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

// Initialize path renderer when DOM is loaded
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