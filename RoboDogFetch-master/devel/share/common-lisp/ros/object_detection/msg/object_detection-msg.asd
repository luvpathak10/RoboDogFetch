
(cl:in-package :asdf)

(defsystem "object_detection-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "TargetInfo" :depends-on ("_package_TargetInfo"))
    (:file "_package_TargetInfo" :depends-on ("_package"))
  ))