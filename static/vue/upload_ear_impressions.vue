<template>
  <div class="ear-upload-container">
    <div
      v-if="showLeftUpload"
      class="ear-upload-box left-ear"
      :class="{ 'has-file': !!leftImpressionDoc, 'dragging': isDraggingLeft, 'disabled': disabled }"
      @click="!disabled ? triggerFileInput('left') : $event.preventDefault()"
      @dragover.prevent="!disabled ? (isDraggingLeft = true) : null"
      @dragleave.prevent="!disabled ? (isDraggingLeft = false) : null"
      @drop.prevent="!disabled ? handleDrop('left', $event) : null"
    >
      <div class="ear-illustration left">
        <img
          src="/static/images/icon ear.png"
          alt="Left Ear Impression"
          class="ear-icon"
        >
      </div>
      <div class="ear-upload-content">
        <h4>Left Ear<span v-if="requireLeftDoc" class="required-mark"> *</span></h4>
        <div class="upload-info">
          <span v-if="!leftImpressionDoc" class="upload-prompt">Click or drag file here</span>
          <span v-else class="uploaded-filename">{{ leftImpressionDoc.name }}</span>
        </div>
        <input
          ref="leftFileInput"
          id="leftImpressionDoc"
          type="file"
          @change="handleFileUpload('left', $event)"
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
          class="hidden-file-input"
        >
      </div>
    </div>

    <div
      v-if="showRightUpload"
      class="ear-upload-box right-ear"
      :class="{ 'has-file': !!rightImpressionDoc, 'dragging': isDraggingRight, 'disabled': disabled }"
      @click="!disabled ? triggerFileInput('right') : $event.preventDefault()"
      @dragover.prevent="!disabled ? (isDraggingRight = true) : null"
      @dragleave.prevent="!disabled ? (isDraggingRight = false) : null"
      @drop.prevent="!disabled ? handleDrop('right', $event) : null"
    >
      <div class="ear-illustration right">
        <img
          src="/static/images/icon ear.png"
          alt="Right Ear Impression"
          class="ear-icon"
        >
      </div>
      <div class="ear-upload-content">
        <h4>Right Ear<span v-if="requireRightDoc" class="required-mark"> *</span></h4>
        <div class="upload-info">
          <span v-if="!rightImpressionDoc" class="upload-prompt">Click or drag file here</span>
          <span v-else class="uploaded-filename">{{ rightImpressionDoc.name }}</span>
        </div>
        <input
          ref="rightFileInput"
          id="rightImpressionDoc"
          type="file"
          @change="handleFileUpload('right', $event)"
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
          class="hidden-file-input"
        >
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UploadEarImpressions',
  props: {
    leftImpressionDoc: {
      type: File,
      default: null
    },
    rightImpressionDoc: {
      type: File,
      default: null
    },
    showLeftUpload: {
      type: Boolean,
      default: true
    },
    showRightUpload: {
      type: Boolean,
      default: true
    },
    requireLeftDoc: {
      type: Boolean,
      default: false
    },
    requireRightDoc: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isDraggingLeft: false,
      isDraggingRight: false
    }
  },
  methods: {
    handleFileUpload(side, event) {
      const file = event.target.files[0];
      if (file) {
        this.$emit('file-upload', { side, file });
      }
    },

    triggerFileInput(side) {
      if (side === 'left') {
        this.$refs.leftFileInput.click();
      } else {
        this.$refs.rightFileInput.click();
      }
    },

    handleDrop(side, event) {
      if (side === 'left') {
        this.isDraggingLeft = false;
      } else {
        this.isDraggingRight = false;
      }

      const files = event.dataTransfer.files;
      if (files.length > 0) {
        const file = files[0];
        // Check file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png'];
        if (allowedTypes.includes(file.type) || file.name.match(/\.(pdf|doc|docx|jpg|jpeg|png)$/i)) {
          this.$emit('file-upload', { side, file });
        }
      }
    }
  }
}
</script>

<style scoped>
/* Ear Upload Container */
.ear-upload-container {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 24px;
  margin-bottom: 24px;
}

.ear-upload-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 3px solid;
  border-radius: 16px;
  background: var(--secondary-color);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  min-height: 280px;
  width: 220px;
  max-width: 220px;
  justify-content: center;
}

.ear-upload-box.left-ear {
  border-color: rgba(59, 130, 246, 0.5);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(59, 130, 246, 0.02));
}

.ear-upload-box.right-ear {
  border-color: rgba(239, 68, 68, 0.5);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(239, 68, 68, 0.02));
}

.ear-upload-box.left-ear:hover {
  border-color: rgba(59, 130, 246, 0.8);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(59, 130, 246, 0.04));
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
}

.ear-upload-box.right-ear:hover {
  border-color: rgba(239, 68, 68, 0.8);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(239, 68, 68, 0.04));
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.2);
}

.ear-upload-box.has-file.left-ear {
  border-color: rgba(59, 130, 246, 1);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0.06));
}

.ear-upload-box.has-file.right-ear {
  border-color: rgba(239, 68, 68, 1);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.06));
}

.ear-upload-box.dragging.left-ear {
  border-color: rgba(59, 130, 246, 1);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.08));
  transform: scale(1.02);
}

.ear-upload-box.dragging.right-ear {
  border-color: rgba(239, 68, 68, 1);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.08));
  transform: scale(1.02);
}

.ear-upload-box.disabled {
  cursor: not-allowed;
  opacity: 0.5;
  position: relative;
}

.ear-upload-box.disabled::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  pointer-events: none;
}

.ear-upload-box.disabled:hover {
  transform: none;
  box-shadow: none;
}

.ear-illustration {
  width: 100px;
  height: 150px;
  margin-bottom: 24px;
}

.ear-illustration.left {
  color: rgba(59, 130, 246, 0.8);
}

.ear-illustration.right {
  color: rgba(239, 68, 68, 0.8);
}

.ear-illustration .ear-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.ear-illustration.left .ear-icon {
  transform: scaleX(-1);
  filter: brightness(0) saturate(100%) invert(20%) sepia(92%) saturate(6500%) hue-rotate(200deg) brightness(100%) opacity(0.8);
}

.ear-illustration.right .ear-icon {
  transform: scaleX(1);
  filter: brightness(0) saturate(100%) invert(14%) sepia(96%) saturate(7000%) hue-rotate(0deg) brightness(95%) opacity(0.8);
}

.ear-upload-content {
  text-align: center;
  width: 100%;
}

.ear-upload-content h4 {
  color: #ffffff;
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
}

.required-mark {
  color: #ef4444;
  margin-left: 4px;
}

.upload-info {
  margin-top: 16px;
  text-align: center;
}

.upload-prompt {
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  display: block;
}

.uploaded-filename {
  color: #10b981;
  font-size: 13px;
  font-weight: 600;
  word-break: break-word;
}

.hidden-file-input {
  display: none;
}

/* Responsive Design */
@media (max-width: 768px) {
  .ear-upload-container {
    flex-direction: column;
    gap: 16px;
    align-items: center;
  }

  .ear-upload-box {
    width: 100%;
    max-width: 300px;
  }
}

@media (max-width: 480px) {
  .ear-upload-container {
    gap: 12px;
  }

  .ear-upload-box {
    min-height: 240px;
    width: 100%;
    max-width: 280px;
  }

  .ear-illustration {
    width: 80px;
    height: 120px;
    margin-bottom: 16px;
  }

  .ear-upload-content h4 {
    font-size: 16px;
  }

  .upload-prompt {
    font-size: 13px;
  }

  .uploaded-filename {
    font-size: 12px;
  }
}
</style>
