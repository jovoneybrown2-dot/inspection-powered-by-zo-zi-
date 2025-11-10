#!/usr/bin/env python3
"""
Script to add photo upload capability to all inspection forms
"""

# Photo button HTML to add to all forms (before closing </form> tag)
PHOTO_BUTTON_HTML = '''
    <!-- PHOTO BUTTON (Floating, Scrolls with Form) -->
    <div class="photo-button-container">
        <button type="button" class="photo-button" onclick="openPhotoModal()">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            Add Photo
        </button>
        <div class="photo-count-badge" id="photoCountBadge">0</div>
    </div>

    <!-- PHOTO MODAL -->
    <div class="photo-modal" id="photoModal">
        <div class="photo-modal-content">
            <div class="photo-modal-header">
                <h3>📷 Add Inspection Photo</h3>
                <button type="button" class="close-modal" onclick="closePhotoModal()">&times;</button>
            </div>

            <div class="photo-input-group">
                <label>Photo Number/Reference:</label>
                <input type="text" id="photoNumber" placeholder="e.g., Photo 1, Item 23, Equipment Issue">
            </div>

            <div class="photo-input-group">
                <label>Comment/Description:</label>
                <textarea id="photoComment" placeholder="Describe what the photo shows..."></textarea>
            </div>

            <input type="file" id="photoFileInput" accept="image/*" capture="environment" onchange="handlePhotoSelect(event)">

            <button type="button" class="capture-photo-btn" onclick="triggerPhotoCapture()">
                📸 Take/Select Photo
            </button>

            <img id="photoPreview" class="photo-preview" style="display: none;">

            <button type="button" class="add-photo-btn" id="addPhotoBtn" onclick="addPhoto()" disabled>
                ✅ Add Photo to Inspection
            </button>

            <div class="photos-list" id="photosList" style="display: none;">
                <h4>📎 Attached Photos (<span id="photosCount">0</span>)</h4>
                <div id="photosContainer"></div>
            </div>
        </div>
    </div>
'''

# CSS for photo buttons and modal
PHOTO_CSS = '''
        /* PHOTO ATTACHMENT STYLES */
        .photo-button-container {
            position: fixed;
            right: 30px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 1000;
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            border: 2px solid #4CAF50;
        }

        .photo-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }

        .photo-button:hover {
            background: #45a049;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }

        .photo-button svg {
            width: 20px;
            height: 20px;
        }

        .photo-count-badge {
            background: #ff5722;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            margin-top: 8px;
        }

        .photo-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 2000;
            justify-content: center;
            align-items: center;
        }

        .photo-modal.active {
            display: flex;
        }

        .photo-modal-content {
            background: white;
            padding: 25px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }

        .photo-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }

        .photo-modal-header h3 {
            margin: 0;
            color: #333;
        }

        .close-modal {
            background: none;
            border: none;
            font-size: 28px;
            cursor: pointer;
            color: #666;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .close-modal:hover {
            color: #000;
        }

        .photo-input-group {
            margin-bottom: 20px;
        }

        .photo-input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }

        .photo-input-group input,
        .photo-input-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }

        .photo-input-group textarea {
            min-height: 80px;
            resize: vertical;
        }

        .photo-preview {
            width: 100%;
            max-height: 300px;
            object-fit: contain;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-top: 10px;
        }

        .capture-photo-btn {
            background: #2196F3;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            width: 100%;
            margin-bottom: 15px;
        }

        .capture-photo-btn:hover {
            background: #1976D2;
        }

        .add-photo-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            width: 100%;
        }

        .add-photo-btn:hover {
            background: #45a049;
        }

        .add-photo-btn:disabled {
            background: #cccccc;
            cursor: not-allowed;
        }

        .photos-list {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
        }

        .photos-list h4 {
            margin-bottom: 15px;
            color: #333;
        }

        .photo-item {
            background: #f9f9f9;
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }

        .photo-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .photo-item-number {
            font-weight: bold;
            color: #4CAF50;
        }

        .delete-photo-btn {
            background: #f44336;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }

        .delete-photo-btn:hover {
            background: #d32f2f;
        }

        .photo-item-comment {
            font-size: 13px;
            color: #666;
            margin-top: 5px;
        }

        .photo-thumbnail {
            width: 60px;
            height: 60px;
            object-fit: cover;
            border-radius: 4px;
            margin-top: 8px;
            cursor: pointer;
        }

        input[type="file"] {
            display: none;
        }
'''

# JavaScript for photo management
PHOTO_JS = '''
        // Photo Management
        let inspectionPhotos = [];
        let currentPhotoData = null;

        function openPhotoModal() {
            document.getElementById('photoModal').classList.add('active');
        }

        function closePhotoModal() {
            document.getElementById('photoModal').classList.remove('active');
            resetPhotoForm();
        }

        function triggerPhotoCapture() {
            document.getElementById('photoFileInput').click();
        }

        function handlePhotoSelect(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                currentPhotoData = e.target.result;
                document.getElementById('photoPreview').src = currentPhotoData;
                document.getElementById('photoPreview').style.display = 'block';
                document.getElementById('addPhotoBtn').disabled = false;
            };
            reader.readAsDataURL(file);
        }

        function addPhoto() {
            const number = document.getElementById('photoNumber').value.trim();
            const comment = document.getElementById('photoComment').value.trim();

            if (!number) {
                alert('Please enter a photo number or reference');
                return;
            }

            if (!currentPhotoData) {
                alert('Please capture or select a photo first');
                return;
            }

            const photo = {
                id: Date.now(),
                number: number,
                comment: comment,
                data: currentPhotoData,
                timestamp: new Date().toISOString()
            };

            inspectionPhotos.push(photo);
            updatePhotosList();
            resetPhotoForm();
            updatePhotoCount();
        }

        function deletePhoto(photoId) {
            if (confirm('Remove this photo from the inspection?')) {
                inspectionPhotos = inspectionPhotos.filter(p => p.id !== photoId);
                updatePhotosList();
                updatePhotoCount();
            }
        }

        function updatePhotosList() {
            const container = document.getElementById('photosContainer');
            const listSection = document.getElementById('photosList');

            if (inspectionPhotos.length === 0) {
                listSection.style.display = 'none';
                return;
            }

            listSection.style.display = 'block';
            document.getElementById('photosCount').textContent = inspectionPhotos.length;

            container.innerHTML = inspectionPhotos.map(photo => `
                <div class="photo-item">
                    <div class="photo-item-header">
                        <span class="photo-item-number">📷 ${photo.number}</span>
                        <button type="button" class="delete-photo-btn" onclick="deletePhoto(${photo.id})">Delete</button>
                    </div>
                    <div class="photo-item-comment">${photo.comment || 'No comment'}</div>
                    <img src="${photo.data}" class="photo-thumbnail" onclick="viewPhotoFullSize('${photo.data}')">
                </div>
            `).join('');
        }

        function viewPhotoFullSize(dataUrl) {
            window.open(dataUrl, '_blank');
        }

        function resetPhotoForm() {
            document.getElementById('photoNumber').value = '';
            document.getElementById('photoComment').value = '';
            document.getElementById('photoFileInput').value = '';
            document.getElementById('photoPreview').style.display = 'none';
            document.getElementById('addPhotoBtn').disabled = true;
            currentPhotoData = null;
        }

        function updatePhotoCount() {
            document.getElementById('photoCountBadge').textContent = inspectionPhotos.length;
        }
'''

print("=" * 60)
print("Photo Support Template Code")
print("=" * 60)
print("\nThis file contains all the HTML, CSS, and JS needed to add")
print("photo support to any inspection form.")
print("\nForms that need photos added:")
print("- ✓ Meat Processing (already done)")
print("- Residential")
print("- Food Establishment")
print("- Small Hotels")
print("- Swimming Pool")
print("- Burial Site")
print("- Barbershop")
print("- Institutional")
print("- Spirit Licence")
print("\nThese templates will need to be updated manually.")
print("=" * 60)
