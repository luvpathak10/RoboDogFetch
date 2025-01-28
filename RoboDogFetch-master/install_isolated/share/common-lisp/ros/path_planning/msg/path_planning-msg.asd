
(cl:in-package :asdf)

(defsystem "path_planning-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "TargetInfo" :depends-on ("_package_TargetInfo"))
    (:file "_package_TargetInfo" :depends-on ("_package"))
  ))