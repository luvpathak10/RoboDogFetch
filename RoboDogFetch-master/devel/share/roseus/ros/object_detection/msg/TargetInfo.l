;; Auto-generated. Do not edit!


(when (boundp 'object_detection::TargetInfo)
  (if (not (find-package "OBJECT_DETECTION"))
    (make-package "OBJECT_DETECTION"))
  (shadow 'TargetInfo (find-package "OBJECT_DETECTION")))
(unless (find-package "OBJECT_DETECTION::TARGETINFO")
  (make-package "OBJECT_DETECTION::TARGETINFO"))

(in-package "ROS")
;;//! \htmlinclude TargetInfo.msg.html


(defclass object_detection::TargetInfo
  :super ros::object
  :slots (_target_type _x _y _z ))

(defmethod object_detection::TargetInfo
  (:init
   (&key
    ((:target_type __target_type) "")
    ((:x __x) 0.0)
    ((:y __y) 0.0)
    ((:z __z) 0.0)
    )
   (send-super :init)
   (setq _target_type (string __target_type))
   (setq _x (float __x))
   (setq _y (float __y))
   (setq _z (float __z))
   self)
  (:target_type
   (&optional __target_type)
   (if __target_type (setq _target_type __target_type)) _target_type)
  (:x
   (&optional __x)
   (if __x (setq _x __x)) _x)
  (:y
   (&optional __y)
   (if __y (setq _y __y)) _y)
  (:z
   (&optional __z)
   (if __z (setq _z __z)) _z)
  (:serialization-length
   ()
   (+
    ;; string _target_type
    4 (length _target_type)
    ;; float32 _x
    4
    ;; float32 _y
    4
    ;; float32 _z
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _target_type
       (write-long (length _target_type) s) (princ _target_type s)
     ;; float32 _x
       (sys::poke _x (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _y
       (sys::poke _y (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _z
       (sys::poke _z (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _target_type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _target_type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _x
     (setq _x (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _y
     (setq _y (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _z
     (setq _z (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get object_detection::TargetInfo :md5sum-) "69b7a3e3b636f94340436ebfca78e609")
(setf (get object_detection::TargetInfo :datatype-) "object_detection/TargetInfo")
(setf (get object_detection::TargetInfo :definition-)
      "string target_type
float32 x
float32 y
float32 z

")



(provide :object_detection/TargetInfo "69b7a3e3b636f94340436ebfca78e609")


