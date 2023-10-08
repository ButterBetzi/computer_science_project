            if "metaKey" in object_configuration:
                target_path = os.path.join(
                    self.destination_dir, object_configuration["targetPath"], "meta.json"
                )
                self.meta_json_handler.update_meta_json(
                    target_path,
                    object_configuration["metaKey"],
                    file_name,
                    "files",
                )

        self.meta_json_handler.create_meta_files_all(self.destination_dir)